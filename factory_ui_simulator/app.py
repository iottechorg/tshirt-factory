from flask import Flask, request, render_template, send_from_directory, jsonify, Response
from flask_cors import CORS
import requests
from io import BytesIO
from managers import (
    initialize_managers, stop_managers,
    machine_manager, production_manager, test_manager, factory_state_manager,
    production_automation, test_automation
)
import logging
import json
import threading
import os
import paho.mqtt.client as mqtt

# Compatibility shim for Python 3.14+: provide pkgutil.get_loader if missing
import pkgutil
import importlib.util
import ast
# Provide missing helpers removed in Python 3.14 used by older deps (werkzeug/flask)
if not hasattr(ast, 'Str'):
    class _CompatStr(ast.Constant):
        def __init__(self, s):
            super().__init__(value=s)
            self.s = s
    ast.Str = _CompatStr
if not hasattr(ast, 'Num'):
    class _CompatNum(ast.Constant):
        def __init__(self, n):
            super().__init__(value=n)
            self.n = n
    ast.Num = _CompatNum
if not hasattr(ast, 'NameConstant'):
    class _CompatNameConstant(ast.Constant):
        def __init__(self, v):
            super().__init__(value=v)
            self.value = v
    ast.NameConstant = _CompatNameConstant

if not hasattr(pkgutil, "get_loader"):
    def _get_loader(name):
        try:
            if not name or name == "__main__":
                return None
            spec = importlib.util.find_spec(name)
            return spec.loader if spec else None
        except Exception:
            return None
    pkgutil.get_loader = _get_loader

from config import (
    FACTORY_SITE_ID, MQTT_BROKER, MQTT_PORT, API_BASE_URL, WEBAPP_PORT,
    MQTT_RESOLVED_URL, MQTT_WS_PORT, CUSTOMER_UI_URL, CUSTOMER_UI_LABEL,
    MACHINE_DATA_REST_REQUEST_INTERVAL, MQTT_TOPIC_PRODUCTION, MQTT_PUBLIC_HOST
)

# Load factory config at startup if available
factory_config = None

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)
CORS(app, resources={r"/*": {"origins": "*"}})


def create_response(data, status_code=200):
    """Helper to create JSON responses."""
    response = jsonify(data)
    response.status_code = status_code
    return response


@app.route("/")
def index():
    """Serve main UI."""
    return render_template('index.html',
                           API_BASE_URL=API_BASE_URL,
                           MQTT_BROKER=MQTT_PUBLIC_HOST,
                           MQTT_WS_PORT=MQTT_WS_PORT,
                           FACTORY_SITE_ID=FACTORY_SITE_ID,
                           CUSTOMER_UI_URL=CUSTOMER_UI_URL,
                           CUSTOMER_UI_LABEL=CUSTOMER_UI_LABEL,
                           MACHINE_DATA_REST_REQUEST_INTERVAL=MACHINE_DATA_REST_REQUEST_INTERVAL,
                           MQTT_TOPIC_PRODUCTION=MQTT_TOPIC_PRODUCTION)


@app.route("/machines", methods=["GET"])
def get_machines():
    """Get list of machines from factory state (via MQTT)."""
    machines = machine_manager.get_machines()
    return create_response(machines)


@app.route("/machines/<string:machine_id>", methods=["PUT"])
def update_machine_rest(machine_id):
    """Update machine settings (e.g., failure_rate, operational parameters)."""
    data = request.get_json()
    machine = machine_manager.update_machine(machine_id, data)
    if not machine:
        return create_response({"message": "Machine not found"}, 404)
    return create_response(machine)


@app.route("/machines/sensor/<string:machine_id>/<string:sensor_name>", methods=["PUT"])
def update_sensor_rest(machine_id, sensor_name):
    """Update sensor value via REST. Publishes command to factory via MQTT."""
    data = request.get_json()
    if 'value' not in data:
        return create_response({"message": "Value is required"}, 400)
    value = data["value"]
    machine = machine_manager.update_machine_sensor(machine_id, sensor_name, value)
    if not machine:
        return create_response({"message": "Machine or sensor not found"}, 404)
    return create_response(machine)


@app.route("/production", methods=["POST"])
def start_production():
    """Submit a production request. Publishes to factory via MQTT."""
    data = request.get_json(silent=True)
    app.logger.debug("Incoming production request: %s", data)
    if not data or "product_name" not in data:
        app.logger.warning("Invalid production request: %s", data)
        return create_response({"message": "product_name is required"}, 400)
    
    product_name = data["product_name"]
    product_details = data.get("product_details", None)
    
    try:
        production_manager.request_production(product_name, product_details)
        app.logger.info(f"Production request submitted: {product_name}")
        return create_response({"message": "Production request sent to factory"}, 202)
    except Exception as e:
        app.logger.exception("Failed to submit production request")
        return create_response({"message": "Internal server error"}, 500)


@app.route("/production/status", methods=["GET"])
def get_production_status():
    """Get current production status from factory."""
    status = production_manager.get_production_status()
    if not status:
        return create_response({"status": "idle"})
    return create_response(status)


@app.route("/production/config", methods=["PUT"])
def update_production_config():
    """Update global production configuration."""
    data = request.get_json()
    if not data:
        return create_response({"message": "Data is required"}, 400)
    
    success = production_manager.update_production_config(data)
    if success:
        return create_response({"message": "Production config update sent to factory"}, 200)
    else:
        return create_response({"message": "Failed to update production config"}, 500)


@app.route("/automation/production/start", methods=["POST"])
def start_production_automation():
    """Start automated random production."""
    try:
        data = request.get_json(silent=True) or {}
        interval = int(data.get("interval_seconds", 5))
        interval = max(1, min(300, interval))  # Clamp 1-300 seconds

        app.logger.info(f"🔄 Starting production automation with {interval}s interval...")
        result = production_automation.start(interval)

        if result.get("status") == "started":
            message = f"✅ Production automation STARTED! Will send product requests every {interval} seconds."
            app.logger.info(f"{message} Status: {result}")
            result["message"] = message
            result["type"] = "success"
        elif result.get("status") == "already_running":
            message = "⚠️ Production automation is already running!"
            app.logger.warning(f"{message} Ignoring duplicate start request")
            result["message"] = message
            result["type"] = "warning"
        else:
            message = "❌ Failed to start production automation. Please try again."
            app.logger.error(f"{message} Result: {result}")
            result["message"] = message
            result["type"] = "error"

        return create_response(result, 202)
    except Exception as e:
        error_msg = f"💥 Error starting production automation: {str(e)}"
        app.logger.exception(error_msg)
        return create_response({
            "message": "Failed to start automation. Check logs for details.",
            "type": "error",
            "error": str(e)
        }, 500)


@app.route("/automation/production/stop", methods=["POST"])
def stop_production_automation():
    """Stop automated random production."""
    try:
        app.logger.info("🛑 Stopping production automation...")
        result = production_automation.stop()

        if result.get("status") == "stopped":
            total_requests = result.get("total_requests", 0)
            message = f"🛑 Production automation STOPPED! Sent {total_requests} product requests during this session."
            app.logger.info(f"{message} Status: {result}")
            result["message"] = message
            result["type"] = "success"
        elif result.get("status") == "not_running":
            message = "⚠️ Production automation was not running."
            app.logger.warning(f"{message} Ignoring stop request")
            result["message"] = message
            result["type"] = "warning"
        else:
            message = "❌ Failed to stop production automation. Please try again."
            app.logger.error(f"{message} Result: {result}")
            result["message"] = message
            result["type"] = "error"

        return create_response(result, 200)
    except Exception as e:
        error_msg = f"💥 Error stopping production automation: {str(e)}"
        app.logger.exception(error_msg)
        return create_response({
            "message": "Failed to stop automation. Check logs for details.",
            "type": "error",
            "error": str(e)
        }, 500)


@app.route("/automation/production/status", methods=["GET"])
def get_production_automation_status():
    """Get production automation status."""
    try:
        status = production_automation.get_status()
        state = status.get("state", "unknown")
        total_requests = status.get("total_requests", 0)
        enabled = status.get("enabled", False)

        if state == "running":
            message = f"▶️ Production automation is RUNNING - {total_requests} requests sent so far."
            status["message"] = message
            status["type"] = "info"
            app.logger.debug(f"📊 Automation STATUS: {message}")
        elif state == "stopped":
            message = f"⏸️ Production automation is STOPPED - {total_requests} total requests sent."
            status["message"] = message
            status["type"] = "info"
            app.logger.debug(f"📊 Automation STATUS: {message}")
        elif state == "idle":
            message = "⏸️ Production automation is IDLE - not started yet."
            status["message"] = message
            status["type"] = "info"
            app.logger.debug(f"📊 Automation STATUS: {message}")
        else:
            message = f"❓ Production automation status: {state}"
            status["message"] = message
            status["type"] = "info"
            app.logger.debug(f"📊 Automation STATUS: {message}")

        return create_response(status)
    except Exception as e:
        error_msg = f"💥 Error getting automation status: {str(e)}"
        app.logger.exception(error_msg)
        return create_response({
            "message": "Failed to get automation status. Check logs for details.",
            "type": "error",
            "error": str(e)
        }, 500)


@app.route("/test_cases.json", methods=["GET"])
def serve_test_cases():
    """Serve test cases configuration."""
    # Prefer factory-specific test cases if present in generated-factories
    gen_path = os.path.join(os.path.dirname(__file__), '..', 'generated-factories', FACTORY_SITE_ID, 'test_cases.json')
    if os.path.exists(gen_path):
        try:
            return send_from_directory(os.path.dirname(gen_path), os.path.basename(gen_path))
        except Exception:
            app.logger.exception(f"Failed to serve {gen_path}")
    
    # Fallback to local static file
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'static'), 'test_cases.json')


@app.route("/test/run/<string:test_case_name>", methods=["POST"])
def run_test_case_route(test_case_name):
    """Run a named test case."""
    try:
        # Load test cases from the same source as /test_cases.json
        gen_path = os.path.join(os.path.dirname(__file__), '..', 'generated-factories', FACTORY_SITE_ID, 'test_cases.json')
        static_path = os.path.join(os.path.dirname(__file__), 'static', 'test_cases.json')
        
        test_cases_file = gen_path if os.path.exists(gen_path) else static_path
        
        with open(test_cases_file, 'r') as f:
            data = json.load(f)
            
        test_case = next((tc for tc in data.get("test_cases", []) if tc.get("name") == test_case_name), None)
        
        if not test_case:
            return create_response({"message": f"Test case '{test_case_name}' not found"}, 404)
        
        test_manager.run_test_case(test_case)
        return create_response({"message": f"Test case '{test_case_name}' started"}, 202)
    except Exception as e:
        app.logger.exception("Error running test case")
        return create_response({"message": str(e)}, 500)











@app.route("/factory-config", methods=["GET"])
def get_factory_config():
    """Get factory configuration (if loaded)."""
    global factory_config
    if factory_config:
        return create_response(factory_config)
    return create_response({}, 404)


@app.route("/factory-config/generated/<string:factory_id>", methods=["GET"])
def get_generated_factory_config(factory_id):
    """Get generated factory config for a specific factory ID."""
    # Try relative path first (original behavior)
    gen_path = os.path.join("..", "generated-factories", factory_id, "factory-config.json")
    app.logger.debug(f"Looking for generated config at {gen_path}")
    if os.path.exists(gen_path):
        try:
            with open(gen_path, 'r') as f:
                cfg = json.load(f)
                return create_response(cfg)
        except Exception as e:
            app.logger.error(f"Error reading factory config: {e}")
            return create_response({"error": "Failed to read generated config"}), 500

    # Fallback: check absolute mounted path (useful if host mount target differs)
    alt_path = os.path.join('/', 'generated-factories', factory_id, 'factory-config.json')
    app.logger.debug(f"Looking for generated config at fallback {alt_path}")
    if os.path.exists(alt_path):
        try:
            with open(alt_path, 'r') as f:
                cfg = json.load(f)
                return create_response(cfg)
        except Exception as e:
            app.logger.error(f"Error reading factory config (fallback): {e}")
            return create_response({"error": "Failed to read generated config (fallback)"}), 500

    return create_response({}), 404


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return create_response({
        "status": "ok",
        "factory_site_id": FACTORY_SITE_ID,
        "mqtt_connected": factory_state_manager.is_connected
    })


@app.route("/proxy-image", methods=["GET"])
def proxy_image():
    """
    Proxy endpoint to fetch images from external services (e.g., pollinations.ai).
    Bypasses client-side CORS/Referer restrictions by fetching server-to-server.
    
    Query params:
      prompt: The image generation prompt (required)
      width: Image width (default 512)
      height: Image height (default 512)
      _t: Cache-busting timestamp (ignored)
    """
    try:
        prompt = request.args.get('prompt')
        if not prompt:
            return create_response({"error": "prompt parameter is required"}, 400)
        
        width = request.args.get('width', '512')
        height = request.args.get('height', '512')
        
        # Build URL to external image service (ignore cache-busting _t parameter)
        # Use quote instead of quote_plus for cleaner URLs in some services
        from urllib.parse import quote
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        encoded_prompt = quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
        app.logger.info(f"Proxying image request for prompt: {prompt}")
        app.logger.debug(f"Target URL: {image_url}")

        # Use a session with retries to tolerate transient failures/timeouts
        session = requests.Session()
        # Add a User-Agent to avoid being blocked as a bot
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
        })
        
        # Be slightly less aggressive with retries to avoid long hangs
        retries = Retry(total=3, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504))
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)

        # Fetch image server-to-server (no browser Referer/CORS issues)
        try:
            # First try a shorter timeout
            app.logger.debug(f"Starting GET request to {image_url}")
            response = session.get(image_url, timeout=45)
            app.logger.debug(f"Received response with status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            app.logger.warning(f"Error fetching image for prompt '{prompt}': {e}")
            # Return a lightweight SVG placeholder so the UI shows an image quickly
            placeholder_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <rect width="100%" height="100%" fill="#1f2937" />
  <circle cx="256" cy="200" r="60" fill="#374151" />
  <path d="M156 350 L256 250 L356 350 Z" fill="#374151" />
  <text x="50%" y="70%" fill="#9ca3af" font-family="Arial,Helvetica,sans-serif" font-size="20" dominant-baseline="middle" text-anchor="middle">Generation in Progress</text>
  <text x="50%" y="78%" fill="#6b7280" font-family="Arial,Helvetica,sans-serif" font-size="14" dominant-baseline="middle" text-anchor="middle">The service is taking longer than usual...</text>
</svg>'''
            return Response(placeholder_svg, mimetype='image/svg+xml', headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'X-Image-Proxy-Error': str(e)[:100]
            })

        content = response.content
        
        if response.status_code != 200:
            app.logger.warning(f"Image service returned {response.status_code} for {image_url}")
            return create_response({"error": f"Failed to fetch image: {response.status_code}"}, response.status_code)

        app.logger.info(f"Successfully fetched image for '{prompt}' ({len(content)} bytes)")
        # Return image with appropriate headers
        mimetype = response.headers.get('content-type', 'image/png')
        return Response(
            content,
            mimetype=mimetype,
            headers={
                'Cache-Control': 'public, max-age=3600', # Allow some caching for successful images
                'X-Image-Original-Url': image_url
            }
        )
    
    except requests.Timeout:
        app.logger.error(f"Timeout fetching image for prompt: {prompt}")
        return create_response({"error": "Image service timeout"}, 504)
    except Exception as e:
        app.logger.exception(f"Error proxying image: {e}")
        return create_response({"error": "Failed to proxy image"}, 500)


if __name__ == "__main__":
    try:
        app.logger.info("Initializing Factory UI Simulator...")
        app.logger.info(f"Factory Site ID: {FACTORY_SITE_ID}")
        app.logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        
        # Initialize MQTT-based managers
        initialize_managers()
        
        # Start Flask web server
        app.logger.info(f"Starting Flask server on port {WEBAPP_PORT}")
        app.run(debug=True, use_reloader=False, host="0.0.0.0", port=WEBAPP_PORT)
    
    except Exception as err:
        app.logger.exception(f"Fatal error: {err}")
        raise
    
    finally:
        app.logger.info("Shutting down...")
        stop_managers()


