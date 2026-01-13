# machine.py
import asyncio
import json
import random
from uuid import uuid4


class Machine:
    def __init__(self, name):
        self.id = str(uuid4())
        self.name = name
        self.is_running = False
        self.runtime_state = "idle"
        self.process_data = {}
        self.sensor_data = self._get_initial_sensors(name)
        self.failure_rate = 0.01  # Default failure rate

    def _get_initial_sensors(self, name):
        if name == "cutting":
            return {
                "blade_temperature": random.randint(25, 35),
                "blade_pressure": random.uniform(1, 1.5),
                "cut_speed": random.uniform(0.1, 0.3),
                "motor_current": random.uniform(0.5, 1.2)
            }
        elif name == "sewing":
            return {
                "needle_temperature": random.randint(28, 38),
                "thread_tension": random.uniform(0.6, 1),
                "stitch_speed": random.uniform(0.15, 0.4),
                "motor_current": random.uniform(0.4, 1.1)
            }
        elif name == "ironing":
            return {
                "plate_temperature": random.randint(100, 150),
                "steam_pressure": random.uniform(0.5, 1),
                "contact_force": random.uniform(0.2, 0.6),
                "energy_consumption": random.uniform(1, 2)
            }
        elif name == "printing":
            return {
                "ink_temperature": random.randint(20, 30),
                "print_speed": random.uniform(0.1, 0.3),
                "nozzle_pressure": random.uniform(0.8, 1.2),
                "material_consumption": random.uniform(0.1, 0.2)
            }
        return {}

    def to_json(self):
        return json.dumps({
            "id": self.id,
            "name": self.name,
            "is_running": self.is_running,
            "runtime_state": self.runtime_state,
            "process_data": self.process_data,
            "sensor_data": self.sensor_data
        })

    def __str__(self):
        return self.to_json()

    async def run(self):
        self.is_running = True
        while self.is_running:
            self.update_sensor_data()
            self.runtime_state = "running" if self.is_running else "idle"
            await asyncio.sleep(random.uniform(1, 3))  # Simulate some runtime variations

    def stop(self):
        self.is_running = False
        self.runtime_state = "idle"

    def update_sensor_data(self):
        if self.name == "cutting":
            self.sensor_data["blade_temperature"] += random.uniform(-0.5, 0.5)
            self.sensor_data["blade_pressure"] += random.uniform(-0.1, 0.1)
            self.sensor_data["cut_speed"] += random.uniform(-0.02, 0.02)
            self.sensor_data["motor_current"] += random.uniform(-0.2, 0.2)
        elif self.name == "sewing":
            self.sensor_data["needle_temperature"] += random.uniform(-0.5, 0.5)
            self.sensor_data["thread_tension"] += random.uniform(-0.1, 0.1)
            self.sensor_data["stitch_speed"] += random.uniform(-0.02, 0.02)
            self.sensor_data["motor_current"] += random.uniform(-0.2, 0.2)
        elif self.name == "ironing":
            self.sensor_data["plate_temperature"] += random.uniform(-1, 1)
            self.sensor_data["steam_pressure"] += random.uniform(-0.1, 0.1)
            self.sensor_data["contact_force"] += random.uniform(-0.05, 0.05)
            self.sensor_data["energy_consumption"] += random.uniform(-0.1, 0.1)
        elif self.name == "printing":
            self.sensor_data["ink_temperature"] += random.uniform(-0.5, 0.5)
            self.sensor_data["print_speed"] += random.uniform(-0.02, 0.02)
            self.sensor_data["nozzle_pressure"] += random.uniform(-0.1, 0.1)
            self.sensor_data["material_consumption"] += random.uniform(-0.01, 0.01)

    def update_sensor_config(self, sensor_name, new_value):
        if sensor_name in self.sensor_data:
            try:
                self.sensor_data[sensor_name] = float(new_value)
                return True
            except ValueError:
                return False
        return False
