from flask import Flask, request, render_template, send_from_directory
from flask_cors import CORS
from managers import *
import logging

app = Flask(__name__)
#app.config['DEBUG'] = True  # Enable debug mode
CORS(app)


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
    #logging.debug(request.get_json())
    data = request.get_json()
    if "product_name" not in data:
        return create_response({"message": "product_name is required"}, 400)
    product_name = data["product_name"]
    product_details = data.get("product_details", None)
    production_manager.add_production_request(product_name, product_details)
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
        production_manager.add_production_request("T-Shirt", generate_random_product_details())
    elif test_case == "high_temp_cutting":
        cutting_machine = next((m for m in machines if m.name == "cutting"), None)
        if cutting_machine:
            machine_manager.update_machine_sensor(cutting_machine.id, "blade_temperature", 40)
        production_manager.add_production_request("T-Shirt", generate_random_product_details())
    elif test_case == "low_thread_tension_sewing":
        sewing_machine = next((m for m in machines if m.name == "sewing"), None)
        if sewing_machine:
            machine_manager.update_machine_sensor(sewing_machine.id, "thread_tension", 0.1)
        production_manager.add_production_request("T-Shirt", generate_random_product_details())
    elif test_case == "high_failure_rate":
        production_manager.production_process.set_failure_rate(0.7)
        production_manager.add_production_request("T-Shirt", generate_random_product_details())
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
        production_manager.add_production_request("T-Shirt", generate_random_product_details())
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
                production_manager.add_production_request(step["product_name"], step["details"])
            elif step["action"] == "update_production_success_rate":
                if step["success_rate"]:
                    production_manager.production_process.set_failure_rate(1 - float(step["success_rate"]))
    return create_response({"message": f"Test case '{test_case}' started"})


if __name__ == "__main__":
    try:
        machine_thread = threading.Thread(target=machine_manager.run)
        publish_thread = threading.Thread(target=machine_manager.publish_machine_data)
        production_thread_setup = threading.Thread(target=production_manager.run)  # daemon to prevent blocking

        machine_thread.start()
        publish_thread.start()
        production_thread_setup.start()

        app.run(debug=True, use_reloader=False, host="0.0.0.0", port=WEBAPP_PORT)
    except Exception as err:
        logging.error(err)

