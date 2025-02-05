import asyncio
from machine import Machine
from production import ProductionProcess
from mqtt_publisher import MQTTPublisher
import threading
import time
import logging

from util import *
from config import *

machines = [Machine(name) for name in MACHINE_NAMES]
machine_mqtt_publisher = MQTTPublisher(client_id="machine_simulator_machine")
production_mqtt_publisher = MQTTPublisher(client_id="machine_simulator_production")

# Move the production process creation inside the production manager
production_process = None


class MachineManager(threading.Thread):
    def __init__(self, all_machines, publisher):
        super().__init__(daemon=True)
        self.machines = all_machines
        self.publisher = publisher
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def run(self):
        self.publisher.connect()
        self.publisher.loop_start()
        machine_tasks = [self.loop.create_task(machine.run()) for machine in self.machines]
        self.loop.run_until_complete(asyncio.gather(*machine_tasks))
        self.loop.close()
        self.publisher.loop_stop()

    def publish_machine_data(self):
        while True:
            try:
                data = [json.loads(machine.to_json()) for machine in self.machines]
                self.publisher.publish(MQTT_TOPIC_MACHINE, json.dumps(data))
            except Exception as e:
                logging.error(f"Error generating or publishing message: {e}")
            time.sleep(MACHINE_DATA_PUBLISH_INTERVAL)

    def update_machine(self, machine_id, data):
        machine = get_machine_by_id(self.machines, machine_id)
        if not machine:
            logging.warning("Machine not found")
            return None
        if "failure_rate" in data:
            machine.failure_rate = float(data["failure_rate"])
        return machine

    def update_machine_sensor(self, machine_id, sensor_name, value):
        machine = get_machine_by_id(self.machines, machine_id)
        if not machine:
            logging.warning(f"Machine not found {machine_id}")
            return None
        if not machine.update_sensor_config(sensor_name, value):
            logging.warning(f"Sensor not found {sensor_name} for {machine_id}")
            return None
        return machine


class ProductionManager(threading.Thread):
    def __init__(self, publisher):
        super().__init__(daemon=True)
        self.publisher = publisher
        self.production_process = ProductionProcess(machines, publisher)

    def run(self):
        self.publisher.connect()
        self.publisher.loop_start()
        while True:
            self.production_process.process_production_request()
            time.sleep(PRODUCTION_LOOP_INTERVAL)

    def add_production_request(self, product_name, product_details=None):
        self.production_process.add_production_request(product_name, product_details)


machine_manager = MachineManager(machines, machine_mqtt_publisher)
production_manager = ProductionManager(production_mqtt_publisher)
