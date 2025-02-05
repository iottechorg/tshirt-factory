import random
import json
from uuid import uuid4
from config import PRODUCTION_SUCCESS_RATE, MQTT_TOPIC_PRODUCTION
import time
import logging

stitch_types = ["Straight", "Zigzag", "Satin", "Blind", "Overlock"]
thread_colors = ["Red", "Green", "Blue", "Black", "White", "Yellow", "Purple"]
steam_levels = ["Low", "Medium", "High", "None"]
ink_types = ["Water-based", "Plastisol", "Discharge", "None"]
iron_temperature_setpoint_min_temp = 100
iron_temperature_setpoint_max_temp = 180

class ProductionProcess:
    def __init__(self, machines, publisher):
        self.machines = machines
        self.production_id = None
        self.steps = ["cutting", "sewing", "ironing", "printing"]
        self.status = "pending"
        self.publisher = publisher
        self.failure_rate = 1 - PRODUCTION_SUCCESS_RATE
        self.production_queue = []

    def process_product_details(self, product_details):
        """
        Checks for stitch_type, thread_color, iron_temperature_setpoint,
        stream_level, and ink_type in a JSON object. Assigns random values
        if the fields are missing or have no assigned value.

        Args:
            product_details: A string representing a JSON object.

        Returns:
            A Python dictionary representing the processed JSON object.
        """

        if not product_details.get("stitch_type"):
            product_details["stitch_type"] = random.choice(stitch_types)

        if not product_details.get("thread_color"):
            product_details["thread_color"] = random.choice(thread_colors)

        if not product_details.get("iron_temperature_setpoint"):
            product_details["iron_temperature_setpoint"] = random.randint(iron_temperature_setpoint_min_temp, iron_temperature_setpoint_max_temp)

        if not product_details.get("steam_level"):
            product_details["steam_level"] = random.choice(steam_levels)

        if not product_details.get("ink_type"):
            product_details["ink_type"] = random.choice(ink_types)
        return product_details

    def add_production_request(self, product_name, product_details=None):
        self.production_queue.append({
            "product_name": product_name,
            "product_details": self.process_product_details(product_details)
        })

    def process_production_request(self):
        if self.production_queue:
            request = self.production_queue.pop(0)
            product_name = request["product_name"]
            product_details = request["product_details"]
            self.production_id = str(uuid4())
            self.status = "running"
            production_data = {
                "production_id": self.production_id,
                "product_name": product_name,
                "product_details": product_details,
                "status": self.status,
                "steps": []
            }
            try:
                for step in self.steps:
                    machine = next((m for m in self.machines if m.name == step), None)
                    if not machine:
                        raise Exception(f"Machine not found for step {step}")

                    if step == "cutting":
                        machine.process_data = {"material": product_details["material"],
                                                "cut_size": product_details["cut_size"]}
                    elif step == "sewing":
                        machine.process_data = {"stitch_type": product_details["stitch_type"],
                                                "thread_color": product_details["thread_color"]}
                    elif step == "ironing":
                        machine.process_data = {
                            "iron_temperature_setpoint": product_details["iron_temperature_setpoint"],
                            "steam_level": product_details["steam_level"]}
                    elif step == "printing":
                        machine.process_data = {"ink_type": product_details["ink_type"]}

                    logging.info(f"Starting {step} process")
                    machine.runtime_state = "busy"
                    step_result = self.process_step(machine, step)
                    production_data["steps"].append(step_result)
                    if step_result["status"] == "failed":
                        self.status = "failed"
                        production_data["status"] = "failed"
                        production_data[step] = "failed"
                        logging.info(f"Production failed at step: {step}")
                        break
                if self.status == "running":
                    self.status = "completed"
                    production_data["status"] = "completed"
                    logging.info(f"Production completed successfully!")
            except Exception as e:
                self.status = "failed"
                production_data["status"] = "failed"
                logging.info(f"Production failed {e}")
            finally:
                for m in self.machines:
                    m.runtime_state = "idle"
            self.publisher.publish(MQTT_TOPIC_PRODUCTION, json.dumps(production_data))

    def process_step(self, machine, step_name):
        time.sleep(random.randint(4, 7))  # Simulate processing time
        # TODO: check the sensor data and production data
        #step_result = {"name": step_name, "process_data": machine.process_data, "sensor_data": machine.sensor_data}
        step_result = {"name": step_name, "process_data": machine.process_data}
        random_value = round(random.uniform(0.5, 1), 2)  # TODO: put here on the top of the file
        if random_value < self.failure_rate:  # Simulating failure based on failure rate
            logging.info(f"{machine.name} process failed!")
            step_result["status"] = "failed"
        else:
            logging.info(f"{machine.name} process completed successfully!")
            step_result["status"] = "success"
        return step_result

    def set_failure_rate(self, failure_rate):
        self.failure_rate = failure_rate
