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
import hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap

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
    MACHINE_DATA_REST_REQUEST_INTERVAL, MQTT_TOPIC_PRODUCTION, MQTT_PUBLIC_HOST,
    HF_TOKEN, HF_MODEL, HF_PROVIDER
)

# Load factory config at startup if available
factory_config = None

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)
CORS(app, resources={r"/*": {"origins": "*"}})

# Setup image cache directory
CACHE_DIR = Path("/tmp/image_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def create_response(data, status_code=200):
    """Helper to create JSON responses."""
    response = jsonify(data)
    response.status_code = status_code
    return response


def get_cache_key(prompt, width, height):
    """Generate a cache key from prompt and dimensions."""
    key_str = f"{prompt}_{width}_{height}"
    return hashlib.sha256(key_str.encode()).hexdigest()


def get_cached_image(prompt, width, height):
    """Try to retrieve image from cache."""
    cache_key = get_cache_key(prompt, width, height)
    cache_file = CACHE_DIR / f"{cache_key}.png"
    
    if cache_file.exists():
        app.logger.info(f"Cache hit for prompt: {prompt[:50]}...")
        try:
            with open(cache_file, 'rb') as f:
                return f.read()
        except Exception as e:
            app.logger.warning(f"Failed to read cache file: {e}")
    
    return None


def save_cached_image(prompt, width, height, image_data):
    """Save image to cache."""
    cache_key = get_cache_key(prompt, width, height)
    cache_file = CACHE_DIR / f"{cache_key}.png"
    
    try:
        with open(cache_file, 'wb') as f:
            f.write(image_data)
        app.logger.info(f"Cached image for prompt: {prompt[:50]}... ({len(image_data)} bytes)")
    except Exception as e:
        app.logger.warning(f"Failed to save cache file: {e}")


def generate_placeholder_image(prompt, width=512, height=512):
    """Generate a simple placeholder image when external service fails."""
    try:
        # Create image with gradient background
        img = Image.new('RGB', (int(width), int(height)), color=(240, 248, 255))
        draw = ImageDraw.Draw(img)
        
        # Try to use a nice font, fallback to default
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except:
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
        
        # Draw border
        border_color = (100, 149, 237)  # Cornflower blue
        draw.rectangle([10, 10, int(width)-10, int(height)-10], outline=border_color, width=3)
        
        # Draw title
        title = "Product Image"
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (int(width) - title_width) // 2
        draw.text((title_x, 40), title, fill=(70, 130, 180), font=title_font)
        
        # Wrap and draw prompt text
        prompt_text = f"Prompt:\n{prompt}"
        wrapped_lines = []
        max_chars = 50
        for line in prompt_text.split('\n'):
            wrapped_lines.extend(textwrap.wrap(line, width=max_chars))
        
        y_offset = 120
        for line in wrapped_lines[:8]:  # Limit to 8 lines
            draw.text((40, y_offset), line, fill=(64, 64, 64), font=text_font)
            y_offset += 35
        
        # Add footer
        footer = "[Placeholder - External service unavailable]"
        footer_bbox = draw.textbbox((0, 0), footer, font=text_font)
        footer_width = footer_bbox[2] - footer_bbox[0]
        draw.text(((int(width) - footer_width) // 2, int(height) - 50), footer, fill=(169, 169, 169), font=text_font)
        
        # Convert to bytes
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        app.logger.info(f"Generated placeholder image for prompt: {prompt[:50]}...")
        return img_bytes.getvalue()
    
    except Exception as e:
        app.logger.error(f"Failed to generate placeholder: {e}")
        # Return a minimal 1x1 PNG as last resort
        minimal_img = Image.new('RGB', (1, 1), color=(200, 200, 200))
        img_bytes = BytesIO()
        minimal_img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.getvalue()


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
    workflow_id = data.get("workflow_id", None)
    quantity = data.get("quantity", 1)
    
    # Validate and clamp quantity
    try:
        quantity = int(quantity)
        if quantity < 1:
            quantity = 1
        elif quantity > 100:
            quantity = 100
    except (ValueError, TypeError):
        quantity = 1
    
    try:
        production_manager.request_production(
            product_name, 
            product_details, 
            workflow_id,
            quantity
        )
        app.logger.info(
            f"Production request submitted: {quantity}x {product_name} "
            f"(workflow: {workflow_id or 'default'})"
        )
        return create_response({
            "message": f"Production request sent to factory: {quantity} items",
            "quantity": quantity
        }, 202)
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


@app.route("/workflows", methods=["GET"])
def get_workflows():
    """Get available workflows for the factory."""
    try:
        # Try to get workflows from factory config first
        global factory_config
        if factory_config and "workflows" in factory_config:
            workflows = factory_config["workflows"]
            return create_response(workflows)
        
        # Fallback: try to load from workflows directory  
        factory_site_id = FACTORY_SITE_ID
        workflows_path = Path(__file__).parent.parent / "generated-factories" / factory_site_id / "workflows"
        
        if workflows_path.exists():
            workflows = []
            for workflow_file in workflows_path.glob("*.json"):
                try:
                    with open(workflow_file, 'r') as f:
                        workflow_data = json.load(f)
                        workflows.append({
                            "workflow_id": workflow_data.get("workflow_id"),
                            "workflow_name": workflow_data.get("workflow_name"),
                            "description": workflow_data.get("description"),
                            "product_type": workflow_data.get("product_type")
                        })
                except Exception as e:
                    app.logger.error(f"Error loading workflow {workflow_file}: {e}")
            
            if workflows:
                return create_response(workflows)
        
        # Last fallback: try main workflows directory
        workflows_path = Path(__file__).parent.parent / "workflows"
        if workflows_path.exists():
            workflows = []
            for workflow_file in workflows_path.glob("*.json"):
                try:
                    with open(workflow_file, 'r') as f:
                        workflow_data = json.load(f)
                        workflows.append({
                            "workflow_id": workflow_data.get("workflow_id"),
                            "workflow_name": workflow_data.get("workflow_name"),
                            "description": workflow_data.get("description"),
                            "product_type": workflow_data.get("product_type")
                        })
                except Exception as e:
                    app.logger.error(f"Error loading workflow {workflow_file}: {e}")
            
            return create_response(workflows)
        
        return create_response([])
    except Exception as e:
        app.logger.error(f"Error fetching workflows: {e}")
        return create_response({"error": "Failed to fetch workflows"}, 500)


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


@app.route("/debug/dns-test", methods=["GET"])
def debug_dns_test():
    """Test DNS resolution and HTTP connectivity from inside the container"""
    import socket
    import requests
    diag = {}
    
    try:
        hostname = "image.pollinations.ai"
        ip = socket.gethostbyname(hostname)
        diag["dns_resolution"] = {"status": "ok", "hostname": hostname, "resolved_ip": ip}
    except Exception as e:
        diag["dns_resolution"] = {"status": "error", "error": str(e)}
    
    try:
        # Test HTTP connectivity with a simple request
        response = requests.get("https://image.pollinations.ai/", timeout=10)
        diag["http_connectivity"] = {"status": "ok", "http_code": response.status_code}
    except Exception as e:
        diag["http_connectivity"] = {"status": "error", "error": str(e)}
    
    app.logger.info(f"Diagnostics: {diag}")
    return create_response(diag)


@app.route("/proxy-image", methods=["GET"])
def proxy_image():
    """
    Generate images using Hugging Face API (FLUX.1-dev model).
    Features:
    - Local caching to avoid repeated API calls
    - Placeholder fallback if generation fails
    
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
        
        # Check cache first
        cached_image = get_cached_image(prompt, width, height)
        if cached_image:
            return Response(
                cached_image,
                mimetype='image/png',
                headers={
                    'Cache-Control': 'public, max-age=86400',
                    'X-Cache': 'HIT'
                }
            )
        
        # Check if HF_TOKEN is configured
        if not HF_TOKEN:
            app.logger.warning("HF_TOKEN not configured. Using placeholder image.")
            placeholder_content = generate_placeholder_image(prompt, width, height)
            save_cached_image(prompt, width, height, placeholder_content)
            return Response(
                placeholder_content,
                mimetype='image/png',
                headers={
                    'Cache-Control': 'public, max-age=3600',
                    'X-Cache': 'FALLBACK',
                    'X-Fallback-Reason': 'hf_token_not_configured'
                }
            )
        
        # Generate image using Hugging Face API
        try:
            from huggingface_hub import InferenceClient
            
            app.logger.info(f"Generating image with Hugging Face for prompt: {prompt[:50]}...")
            app.logger.debug(f"Model: {HF_MODEL}, Provider: {HF_PROVIDER}")
            
            client = InferenceClient(
                provider=HF_PROVIDER,
                api_key=HF_TOKEN,
            )
            
            # Generate image (PIL.Image object)
            pil_image = client.text_to_image(
                prompt,
                model=HF_MODEL,
            )
            
            # Convert PIL image to PNG bytes
            img_bytes = BytesIO()
            pil_image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            image_content = img_bytes.getvalue()
            
            # Cache the generated image
            save_cached_image(prompt, width, height, image_content)
            
            app.logger.info(f"Successfully generated image ({len(image_content)} bytes)")
            return Response(
                image_content,
                mimetype='image/png',
                headers={
                    'Cache-Control': 'public, max-age=86400',
                    'X-Cache': 'MISS',
                    'X-Generator': 'huggingface'
                }
            )
        
        except ImportError:
            app.logger.error("huggingface_hub not installed. Using placeholder image.")
            placeholder_content = generate_placeholder_image(prompt, width, height)
            save_cached_image(prompt, width, height, placeholder_content)
            return Response(
                placeholder_content,
                mimetype='image/png',
                headers={
                    'Cache-Control': 'public, max-age=3600',
                    'X-Cache': 'FALLBACK',
                    'X-Fallback-Reason': 'huggingface_hub_not_installed'
                }
            )
        
        except Exception as hf_error:
            app.logger.warning(f"Hugging Face image generation failed: {hf_error}")
            # Generate placeholder as fallback
            placeholder_content = generate_placeholder_image(prompt, width, height)
            save_cached_image(prompt, width, height, placeholder_content)
            return Response(
                placeholder_content,
                mimetype='image/png',
                headers={
                    'Cache-Control': 'public, max-age=3600',
                    'X-Cache': 'FALLBACK',
                    'X-Fallback-Reason': 'generation_error'
                }
            )
    
    except Exception as e:
        app.logger.exception(f"Error in proxy_image: {e}")
        try:
            placeholder_content = generate_placeholder_image(prompt, width, height)
            return Response(
                placeholder_content,
                mimetype='image/png',
                headers={'X-Cache': 'FALLBACK'}
            )
        except:
            return create_response({"error": "Failed to generate image"}, 500)


@app.route("/cache-info", methods=["GET"])
def cache_info():
    """Get cache statistics and HF configuration."""
    try:
        cache_files = list(CACHE_DIR.glob("*.png"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return create_response({
            "cache_enabled": True,
            "cache_dir": str(CACHE_DIR),
            "cached_images": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "image_generator": {
                "type": "huggingface",
                "model": HF_MODEL,
                "provider": HF_PROVIDER,
                "token_configured": bool(HF_TOKEN)
            },
            "note": "Images are cached locally. If HF_TOKEN is not set, placeholder images will be generated."
        })
    except Exception as e:
        app.logger.error(f"Error getting cache info: {e}")
        return create_response({"error": str(e)}, 500)


@app.route("/cache-clear", methods=["POST"])
def cache_clear():
    """Clear the image cache."""
    try:
        cache_files = list(CACHE_DIR.glob("*.png"))
        for f in cache_files:
            f.unlink()
        
        app.logger.info(f"Cleared {len(cache_files)} cached images")
        return create_response({
            "message": f"Cleared {len(cache_files)} cached images",
            "status": "ok"
        })
    except Exception as e:
        app.logger.error(f"Error clearing cache: {e}")
        return create_response({"error": str(e)}, 500)


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


