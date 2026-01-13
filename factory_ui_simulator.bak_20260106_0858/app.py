from flask import Flask, request, render_template, send_from_directory, jsonify
from flask_cors import CORS
from managers import *
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

# runtime-loaded factory config
factory_config = None

app = Flask(__name__)
#app.config['DEBUG'] = True  # Enable debug mode
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)
CORS(app, resources={r"/*": {"origins": ["http://localhost:8080", "http://127.0.0.1:8080"]}})


def send_production_request_to_orchestrator(product_name, product_details):
    """Send production request to orchestrator via MQTT"""
    request_topic = f"factory/{FACTORY_SITE_ID}/production/request"
    request_data = {
        "product_type": "tshirt",
        "product_details": product_details
    }
    production_mqtt_publisher.publish(request_topic, json.dumps(request_data))


def apply_factory_config(cfg: dict):
    """Apply selected parts of the factory config at runtime.

    This updates the production workflow steps and some runtime intervals
    so the simulator can adapt without a full restart.
    """
    global factory_config
    factory_config = cfg
    try:
        workflows = cfg.get("workflows", [])
        if workflows:
            # prefer a workflow that matches 'tshirt' product_type, otherwise pick first
            wf = next((w for w in workflows if w.get("product_type") == "tshirt"), workflows[0])
            steps = [s.get("machine_type") for s in wf.get("steps", []) if s.get("machine_type")]
            if steps:
                production_manager.production_process.steps = steps
                app.logger.info(f"Updated production workflow steps: {steps}")

        # Optional runtime overrides
        # Update managers' intervals if provided in config
        import managers as managers_mod
        if cfg.get("machine_data_publish_interval"):
            managers_mod.MACHINE_DATA_PUBLISH_INTERVAL = int(cfg["machine_data_publish_interval"])
            app.logger.info("Updated MACHINE_DATA_PUBLISH_INTERVAL")
        if cfg.get("production_loop_interval"):
            managers_mod.PRODUCTION_LOOP_INTERVAL = int(cfg["production_loop_interval"])
            app.logger.info("Updated PRODUCTION_LOOP_INTERVAL")
    except Exception as e:
        app.logger.exception("Failed to apply factory config")


@app.route("/factory-config", methods=["GET"])
def get_factory_config():
    if factory_config:
        return jsonify(factory_config)
    # try to load runtime file if exists
    if os.path.exists("factory_config_runtime.json"):
        try:
            with open("factory_config_runtime.json", "r") as f:
                cfg = json.load(f)
                return jsonify(cfg)
        except Exception:
            pass
    return jsonify({}), 404


@app.route("/factory-config/generated/<string:factory_id>", methods=["GET"])
def get_generated_factory_config(factory_id):
    """Return the generated factory-config.json for a given factory id, if present."""
    gen_path = os.path.join("..", "generated-factories", factory_id, "factory-config.json")
    if os.path.exists(gen_path):
        try:
            with open(gen_path, 'r') as f:
                cfg = json.load(f)
                return jsonify(cfg)
        except Exception:
            return jsonify({"error": "Failed to read generated config"}), 500
    return jsonify({}), 404


@app.route("/")
def index():
    return render_template('index.html',
                           API_BASE_URL=API_BASE_URL,
                           MQTT_BROKER=MQTT_RESOLVED_URL,
                           MQTT_WS_PORT=MQTT_WS_PORT,
                           MQTT_TOPIC_PRODUCTION=MQTT_TOPIC_PRODUCTION,
                           MACHINE_DATA_REST_REQUEST_INTERVAL=MACHINE_DATA_REST_REQUEST_INTERVAL)


@app.route("/machines", methods=["GET"])
def get_machines():
    return create_response([json.loads(machine.to_json()) for machine in machines])


@app.route('/test_cases.json', methods=['GET'])
def serve_test_cases():
    return send_from_directory('./static', 'test_cases.json')


@app.route("/machines/<string:machine_id>", methods=["PUT"])
def update_machine_rest(machine_id):
    data = request.get_json()
    machine = machine_manager.update_machine(machine_id, data)
    if not machine:
        return create_response({"message": "Machine not found"}, 404)
    return create_response(json.loads(machine.to_json()))


@app.route("/machines/sensor/<string:machine_id>/<string:sensor_name>", methods=["PUT"])
def update_sensor_rest(machine_id, sensor_name):
    data = request.get_json()
    if 'value' not in data:
        return create_response({"message": "Value is required"}, 400)
    value = data["value"]
    machine = machine_manager.update_machine_sensor(machine_id, sensor_name, value)
    if not machine:
        return create_response({"message": "Machine or sensor not found"}, 404)
    return create_response(json.loads(machine.to_json()))


@app.route("/production", methods=["POST"])
def start_production():
    data = request.get_json(silent=True)
    app.logger.debug("Incoming production request: %s", data)
    if not data or "product_name" not in data:
        app.logger.warning("Invalid production request: %s", data)
        return create_response({"message": "product_name is required"}, 400)
    product_name = data["product_name"]
    product_details = data.get("product_details", None)
    try:
        send_production_request_to_orchestrator(product_name, product_details)
    except Exception as e:
        app.logger.exception("Failed to enqueue production request")
        return create_response({"message": "Internal server error"}, 500)
    return create_response({"message": "Production request added to queue"}, 202)


@app.route("/production/config", methods=["PUT"])
def update_production_config():
    data = request.get_json()
    if "success_rate" in data:
        production_manager.production_process.set_failure_rate(1 - float(data["success_rate"]))
    return create_response({"message": "Production config updated"})


@app.route("/test/<string:test_case>", methods=["POST"])
def trigger_test_case(test_case):
    if test_case == "normal_production":
        send_production_request_to_orchestrator("T-Shirt", generate_random_product_details())
    elif test_case == "high_temp_cutting":
        cutting_machine = next((m for m in machines if m.name == "cutting"), None)
        if cutting_machine:
            machine_manager.update_machine_sensor(cutting_machine.id, "blade_temperature", 40)
        send_production_request_to_orchestrator("T-Shirt", generate_random_product_details())
    elif test_case == "low_thread_tension_sewing":
        sewing_machine = next((m for m in machines if m.name == "sewing"), None)
        if sewing_machine:
            machine_manager.update_machine_sensor(sewing_machine.id, "thread_tension", 0.1)
        send_production_request_to_orchestrator("T-Shirt", generate_random_product_details())
    elif test_case == "high_failure_rate":
        production_manager.production_process.set_failure_rate(0.7)
        send_production_request_to_orchestrator("T-Shirt", generate_random_product_details())
    elif test_case == "sensor_check":
        machines_status = {}
        for m in machines:
            if m.name == "cutting":
                machine_manager.update_machine_sensor(m.id, "blade_temperature", 32)
                machine_manager.update_machine_sensor(m.id, "blade_pressure", 1.3)
            if m.name == "sewing":
                machine_manager.update_machine_sensor(m.id, "needle_temperature", 34)
                machine_manager.update_machine_sensor(m.id, "thread_tension", 0.8)
            if m.name == "ironing":
                machine_manager.update_machine_sensor(m.id, "plate_temperature", 130)
                machine_manager.update_machine_sensor(m.id, "steam_pressure", 0.7)
            if m.name == "printing":
                machine_manager.update_machine_sensor(m.id, "ink_temperature", 25)
                machine_manager.update_machine_sensor(m.id, "nozzle_pressure", 1)
            machines_status[m.name] = m.sensor_data
        logging.info(f"Sensor values for machines are: {machines_status}")
        send_production_request_to_orchestrator("T-Shirt", generate_random_product_details())
    elif test_case == "random_test":
        machines_data = get_machines()
        test_case = generate_random_test_case(json.loads(machines_data.data))
        for step in test_case["steps"]:
            if step["action"] == "update_sensor":
                machines_data = get_machines()
                machine = next((m for m in json.loads(machines_data.data) if m["name"] == step["machine_name"]), None)
                if machine:
                    machine_manager.update_machine_sensor(machine["id"], step["sensor_name"], step["value"])
            elif step["action"] == "update_failure_rate":
                machines_data = get_machines()
                machine = next((m for m in json.loads(machines_data.data) if m["name"] == step["machine_name"]), None)
                if machine:
                    machine_manager.update_machine(machine["id"], {"failure_rate": step["failure_rate"]})
            elif step["action"] == "production_request":
                send_production_request_to_orchestrator(step["product_name"], step["details"])
            elif step["action"] == "update_production_success_rate":
                if step["success_rate"]:
                    production_manager.production_process.set_failure_rate(1 - float(step["success_rate"]))
    return create_response({"message": f"Test case '{test_case}' started"})


if __name__ == "__main__":
    try:
        # Start MQTT client to listen for factory config messages
        mqtt_client = mqtt.Client(client_id=f"factory_ui_config_{FACTORY_SITE_ID}")

        def _on_connect(client, userdata, flags, rc):
            if rc == 0:
                app.logger.info("Connected to MQTT broker for factory config")
                client.subscribe(f"factory/{FACTORY_SITE_ID}/config")
                client.subscribe(f"factory/{FACTORY_SITE_ID}/config/request")
            else:
                app.logger.error(f"Config MQTT connection failed rc={rc}")

        def _on_message(client, userdata, msg):
            try:
                payload = msg.payload.decode("utf-8")
                app.logger.info(f"Factory config message received on {msg.topic}")
                cfg = json.loads(payload)
                # persist runtime copy
                with open("factory_config_runtime.json", "w") as f:
                    json.dump(cfg, f)
                apply_factory_config(cfg)
            except Exception:
                app.logger.exception("Error handling factory config message")

        mqtt_client.on_connect = _on_connect
        mqtt_client.on_message = _on_message
        try:
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            mqtt_client.loop_start()
        except Exception:
            app.logger.exception("Unable to start MQTT config client")

        machine_thread = threading.Thread(target=machine_manager.run)
        publish_thread = threading.Thread(target=machine_manager.publish_machine_data)
        production_thread_setup = threading.Thread(target=production_manager.run)  # daemon to prevent blocking

        machine_thread.start()
        publish_thread.start()
        production_thread_setup.start()

        app.run(debug=True, use_reloader=False, host="0.0.0.0", port=WEBAPP_PORT)
    except Exception as err:
        logging.error(err)

