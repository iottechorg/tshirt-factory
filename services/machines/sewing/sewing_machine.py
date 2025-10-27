"""
Sewing Machine Service
"""
import sys
import os
import random
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../shared'))
from base_machine import BaseMachine

logger = logging.getLogger(__name__)


class SewingMachine(BaseMachine):
    """Sewing machine implementation"""

    def __init__(self, machine_id: str, machine_name: str = "sewing"):
        super().__init__(machine_id, "sewing", machine_name)

    def _initialize_sensors(self):
        """Initialize sewing machine specific sensors"""
        return {
            "needle_temperature": random.uniform(28, 38),
            "thread_tension": random.uniform(0.6, 1.0),
            "stitch_speed": random.uniform(0.15, 0.4),
            "motor_current": random.uniform(0.4, 1.1)
        }

    def update_sensors(self):
        """Update sensor values with small variations"""
        self.sensor_data["needle_temperature"] += random.uniform(-0.5, 0.5)
        self.sensor_data["thread_tension"] += random.uniform(-0.1, 0.1)
        self.sensor_data["stitch_speed"] += random.uniform(-0.02, 0.02)
        self.sensor_data["motor_current"] += random.uniform(-0.2, 0.2)

        # Keep values in reasonable ranges
        self.sensor_data["needle_temperature"] = max(20, min(50, self.sensor_data["needle_temperature"]))
        self.sensor_data["thread_tension"] = max(0.3, min(1.5, self.sensor_data["thread_tension"]))
        self.sensor_data["stitch_speed"] = max(0.1, min(0.6, self.sensor_data["stitch_speed"]))
        self.sensor_data["motor_current"] = max(0.2, min(1.5, self.sensor_data["motor_current"]))

    def validate_process_data(self, process_data):
        """Validate sewing process data"""
        required_fields = ["stitch_type", "thread_color"]
        return all(field in process_data for field in required_fields)
