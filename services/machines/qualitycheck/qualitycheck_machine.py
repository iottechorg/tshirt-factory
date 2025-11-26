"""
Quality Check Machine Service
Inspects products for defects and quality standards
"""
import sys
import os
import random
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), './shared'))
from base_machine import BaseMachine

logger = logging.getLogger(__name__)


class QualityCheckMachine(BaseMachine):
    """Quality inspection machine implementation"""

    def __init__(self, machine_id: str, machine_name: str = "quality-check"):
        super().__init__(machine_id, "quality-check", machine_name)

    def _initialize_sensors(self):
        """Initialize quality check machine specific sensors"""
        return {
            "camera_temperature": random.uniform(25, 35),      # Camera sensor temp
            "light_intensity": random.uniform(800, 1200),      # Inspection light level (lux)
            "scan_speed": random.uniform(0.5, 1.5),           # Items per second
            "defect_detection_rate": random.uniform(0.95, 0.99) # AI model accuracy
        }

    def update_sensors(self):
        """Update sensor values with small variations"""
        self.sensor_data["camera_temperature"] += random.uniform(-0.3, 0.3)
        self.sensor_data["light_intensity"] += random.uniform(-50, 50)
        self.sensor_data["scan_speed"] += random.uniform(-0.1, 0.1)
        self.sensor_data["defect_detection_rate"] += random.uniform(-0.01, 0.01)

        # Keep values in reasonable ranges
        self.sensor_data["camera_temperature"] = max(20, min(40, self.sensor_data["camera_temperature"]))
        self.sensor_data["light_intensity"] = max(500, min(1500, self.sensor_data["light_intensity"]))
        self.sensor_data["scan_speed"] = max(0.3, min(2.0, self.sensor_data["scan_speed"]))
        self.sensor_data["defect_detection_rate"] = max(0.90, min(0.99, self.sensor_data["defect_detection_rate"]))

    def validate_process_data(self, process_data):
        """Validate quality check process data"""
        # Quality check needs the product to inspect
        required_fields = ["product_to_inspect"]
        return all(field in process_data for field in required_fields)
