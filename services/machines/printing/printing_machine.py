"""
Printing Machine Service
"""
import sys
import os
import random
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), './shared'))
from base_machine import BaseMachine

logger = logging.getLogger(__name__)


class PrintingMachine(BaseMachine):
    """Printing machine implementation"""

    def __init__(self, machine_id: str, machine_name: str = "printing"):
        super().__init__(machine_id, "printing", machine_name)

    def _initialize_sensors(self):
        """Initialize printing machine specific sensors"""
        return {
            "ink_temperature": random.uniform(20, 30),
            "print_speed": random.uniform(0.1, 0.3),
            "nozzle_pressure": random.uniform(0.8, 1.2),
            "material_consumption": random.uniform(0.1, 0.2)
        }

    def update_sensors(self):
        """Update sensor values with small variations"""
        self.sensor_data["ink_temperature"] += random.uniform(-0.5, 0.5)
        self.sensor_data["print_speed"] += random.uniform(-0.02, 0.02)
        self.sensor_data["nozzle_pressure"] += random.uniform(-0.1, 0.1)
        self.sensor_data["material_consumption"] += random.uniform(-0.01, 0.01)

        # Keep values in reasonable ranges
        self.sensor_data["ink_temperature"] = max(15, min(40, self.sensor_data["ink_temperature"]))
        self.sensor_data["print_speed"] = max(0.05, min(0.5, self.sensor_data["print_speed"]))
        self.sensor_data["nozzle_pressure"] = max(0.5, min(1.5, self.sensor_data["nozzle_pressure"]))
        self.sensor_data["material_consumption"] = max(0.05, min(0.3, self.sensor_data["material_consumption"]))

    def validate_process_data(self, process_data):
        """Validate printing process data"""
        required_fields = ["ink_type"]
        return all(field in process_data for field in required_fields)
