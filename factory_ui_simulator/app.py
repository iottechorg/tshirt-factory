from flask import Flask, request, render_template, send_from_directory, jsonify
from flask_cors import CORS
from managers import (
    initialize_managers, stop_managers,
    machine_manager, production_manager, test_manager, factory_state_manager
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
    MACHINE_DATA_REST_REQUEST_INTERVAL, MQTT_TOPIC_PRODUCTION
)

# Load factory config at startup if available
factory_config = None

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)
CORS(app, resources={r"/*": {"origins": ["http://localhost:8080", "http://127.0.0.1:8080"]}})


def create_response(data, status_code=200):
    """Helper to create JSON responses."""
    return jsonify(data), status_code


@app.route("/")
def index():
    """Serve main UI."""
    return render_template('index.html',
                           API_BASE_URL=API_BASE_URL,
                           MQTT_BROKER=MQTT_RESOLVED_URL,
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


@app.route('/test_cases.json', methods=['GET'])
def serve_test_cases():
    """Serve test cases configuration."""
    # Prefer factory-specific test cases if present in generated-factories
    gen_path = os.path.join('..', 'generated-factories', FACTORY_SITE_ID, 'test_cases.json')
    if os.path.exists(gen_path):
        try:
            return send_from_directory(os.path.dirname(gen_path), os.path.basename(gen_path))
        except Exception:
            app.logger.exception(f"Failed to serve {gen_path}")
    return send_from_directory('./static', 'test_cases.json')


@app.route("/test/run/<string:test_case_name>", methods=["POST"])
def run_test_case(test_case_name):
    """
    Run a named test case by publishing it to the factory.
    
    Test case format:
    {
        "name": "test_name",
        "description": "...",
        "steps": [
            {"action": "update_sensor", "machine_id": "...", "sensor_name": "...", "value": ...},
            {"action": "production_request", "product_name": "...", "product_details": {...}},
            {"action": "delay", "seconds": 5},
            ...
        ]
    }
    """
    try:
        # Load test case definition
        # Prefer per-generated-factory test cases if present
        test_cases_paths = [
            os.path.join('..', 'generated-factories', FACTORY_SITE_ID, 'test_cases.json'),
            './static/test_cases.json'
        ]
        test_cases_data = {}
        for p in test_cases_paths:
            if os.path.exists(p):
                try:
                    with open(p, 'r') as f:
                        test_cases_data = json.load(f)
                    app.logger.info(f"Loaded test cases from {p}")
                    break
                except Exception as e:
                    app.logger.error(f"Failed to load test cases from {p}: {e}")
                    continue
        # Find the test case by name
        test_case = None
        for tc in test_cases_data.get("test_cases", []) if isinstance(test_cases_data, dict) else []:
            if tc.get("name") == test_case_name:
                test_case = tc
                break
        
        if not test_case:
            return create_response({"message": f"Test case '{test_case_name}' not found"}, 404)
        
        # Send test case to factory
        test_manager.run_test_case(test_case)
        app.logger.info(f"Test case submitted: {test_case_name}")
        return create_response({"message": f"Test case '{test_case_name}' sent to factory"}, 202)
    
    except FileNotFoundError:
        app.logger.error("Test cases file not found")
        return create_response({"message": "Test cases file not found"}, 500)
    except Exception as e:
        app.logger.exception(f"Error running test case: {e}")
        return create_response({"message": "Internal server error"}, 500)


@app.route("/factory-config", methods=["GET"])
def get_factory_config():
    """Get factory configuration (if loaded)."""
    global factory_config
    if factory_config:
        return create_response(factory_config)
    return create_response({}), 404


@app.route("/factory-config/generated/<string:factory_id>", methods=["GET"])
def get_generated_factory_config(factory_id):
    """Get generated factory config for a specific factory ID."""
    gen_path = os.path.join("..", "generated-factories", factory_id, "factory-config.json")
    if os.path.exists(gen_path):
        try:
            with open(gen_path, 'r') as f:
                cfg = json.load(f)
                return create_response(cfg)
        except Exception as e:
            app.logger.error(f"Error reading factory config: {e}")
            return create_response({"error": "Failed to read generated config"}), 500
    return create_response({}), 404


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return create_response({
        "status": "ok",
        "factory_site_id": FACTORY_SITE_ID,
        "mqtt_connected": factory_state_manager.is_connected
    })


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


