"""
Ironing Machine Service
"""
import sys
import os
import random
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../shared'))
from base_machine import BaseMachine

logger = logging.getLogger(__name__)


class IroningMachine(BaseMachine):
    """Ironing machine implementation"""

    def __init__(self, machine_id: str, machine_name: str = "ironing"):
        super().__init__(machine_id, "ironing", machine_name)

    def _initialize_sensors(self):
        """Initialize ironing machine specific sensors"""
        return {
            "plate_temperature": random.uniform(100, 150),
            "steam_pressure": random.uniform(0.5, 1.0),
            "contact_force": random.uniform(0.2, 0.6),
            "energy_consumption": random.uniform(1.0, 2.0)
        }

    def update_sensors(self):
        """Update sensor values with small variations"""
        self.sensor_data["plate_temperature"] += random.uniform(-1.0, 1.0)
        self.sensor_data["steam_pressure"] += random.uniform(-0.1, 0.1)
        self.sensor_data["contact_force"] += random.uniform(-0.05, 0.05)
        self.sensor_data["energy_consumption"] += random.uniform(-0.1, 0.1)

        # Keep values in reasonable ranges
        self.sensor_data["plate_temperature"] = max(80, min(200, self.sensor_data["plate_temperature"]))
        self.sensor_data["steam_pressure"] = max(0.2, min(1.5, self.sensor_data["steam_pressure"]))
        self.sensor_data["contact_force"] = max(0.1, min(1.0, self.sensor_data["contact_force"]))
        self.sensor_data["energy_consumption"] = max(0.5, min(3.0, self.sensor_data["energy_consumption"]))

    def validate_process_data(self, process_data):
        """Validate ironing process data"""
        required_fields = ["iron_temperature_setpoint", "steam_level"]
        return all(field in process_data for field in required_fields)
