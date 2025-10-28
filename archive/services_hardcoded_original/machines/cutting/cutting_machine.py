"""
Cutting Machine Service
"""
import sys
import os
import random
import logging

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../shared'))

from base_machine import BaseMachine

logger = logging.getLogger(__name__)


class CuttingMachine(BaseMachine):
    """Cutting machine implementation"""

    def __init__(self, machine_id: str, machine_name: str = "cutting"):
        super().__init__(machine_id, "cutting", machine_name)

    def _initialize_sensors(self):
        """Initialize cutting machine specific sensors"""
        return {
            "blade_temperature": random.uniform(25, 35),
            "blade_pressure": random.uniform(1.0, 1.5),
            "cut_speed": random.uniform(0.1, 0.3),
            "motor_current": random.uniform(0.5, 1.2)
        }

    def update_sensors(self):
        """Update sensor values with small variations"""
        self.sensor_data["blade_temperature"] += random.uniform(-0.5, 0.5)
        self.sensor_data["blade_pressure"] += random.uniform(-0.1, 0.1)
        self.sensor_data["cut_speed"] += random.uniform(-0.02, 0.02)
        self.sensor_data["motor_current"] += random.uniform(-0.2, 0.2)

        # Keep values in reasonable ranges
        self.sensor_data["blade_temperature"] = max(20, min(45, self.sensor_data["blade_temperature"]))
        self.sensor_data["blade_pressure"] = max(0.5, min(2.0, self.sensor_data["blade_pressure"]))
        self.sensor_data["cut_speed"] = max(0.05, min(0.5, self.sensor_data["cut_speed"]))
        self.sensor_data["motor_current"] = max(0.3, min(1.5, self.sensor_data["motor_current"]))

    def validate_process_data(self, process_data):
        """Validate cutting process data"""
        required_fields = ["material", "cut_size"]
        return all(field in process_data for field in required_fields)
