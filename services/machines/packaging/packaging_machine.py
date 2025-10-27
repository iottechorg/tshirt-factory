"""
Packaging Machine Service
Packages finished products for shipping
"""
import sys
import os
import random
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../shared'))
from base_machine import BaseMachine

logger = logging.getLogger(__name__)


class PackagingMachine(BaseMachine):
    """Packaging machine implementation"""

    def __init__(self, machine_id: str, machine_name: str = "packaging"):
        super().__init__(machine_id, "packaging", machine_name)

    def _initialize_sensors(self):
        """Initialize packaging machine specific sensors"""
        return {
            "sealing_temperature": random.uniform(140, 180),   # Heat sealer temp (°C)
            "conveyor_speed": random.uniform(0.5, 1.2),       # Meters per second
            "label_dispenser_level": random.uniform(70, 100), # Label stock percentage
            "packaging_rate": random.uniform(20, 40)          # Items per minute
        }

    def update_sensors(self):
        """Update sensor values with small variations"""
        self.sensor_data["sealing_temperature"] += random.uniform(-2.0, 2.0)
        self.sensor_data["conveyor_speed"] += random.uniform(-0.05, 0.05)
        self.sensor_data["label_dispenser_level"] += random.uniform(-1.0, 0)  # Labels get used
        self.sensor_data["packaging_rate"] += random.uniform(-2.0, 2.0)

        # Keep values in reasonable ranges
        self.sensor_data["sealing_temperature"] = max(120, min(200, self.sensor_data["sealing_temperature"]))
        self.sensor_data["conveyor_speed"] = max(0.3, min(1.5, self.sensor_data["conveyor_speed"]))
        self.sensor_data["label_dispenser_level"] = max(0, min(100, self.sensor_data["label_dispenser_level"]))
        self.sensor_data["packaging_rate"] = max(10, min(50, self.sensor_data["packaging_rate"]))

    def validate_process_data(self, process_data):
        """Validate packaging process data"""
        required_fields = ["finished_product", "package_type"]
        return all(field in process_data for field in required_fields)
