"""
Folding Machine Service
Folds garments for presentation or packaging
"""
import sys
import os
import random
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), './shared'))
from base_machine import BaseMachine

logger = logging.getLogger(__name__)


class FoldingMachine(BaseMachine):
    """Folding machine implementation"""

    def __init__(self, machine_id: str, machine_name: str = "folding"):
        super().__init__(machine_id, "folding", machine_name)

    def _initialize_sensors(self):
        """Initialize folding machine specific sensors"""
        return {
            "arm_position_x": random.uniform(0, 100),        # Robotic arm X position (cm)
            "arm_position_y": random.uniform(0, 80),         # Robotic arm Y position (cm)
            "gripper_pressure": random.uniform(0.5, 1.5),   # Gripper force (kg)
            "folding_speed": random.uniform(5, 15)          # Folds per minute
        }

    def update_sensors(self):
        """Update sensor values with small variations"""
        self.sensor_data["arm_position_x"] += random.uniform(-5, 5)
        self.sensor_data["arm_position_y"] += random.uniform(-5, 5)
        self.sensor_data["gripper_pressure"] += random.uniform(-0.1, 0.1)
        self.sensor_data["folding_speed"] += random.uniform(-1.0, 1.0)

        # Keep values in reasonable ranges
        self.sensor_data["arm_position_x"] = max(0, min(100, self.sensor_data["arm_position_x"]))
        self.sensor_data["arm_position_y"] = max(0, min(80, self.sensor_data["arm_position_y"]))
        self.sensor_data["gripper_pressure"] = max(0.3, min(2.0, self.sensor_data["gripper_pressure"]))
        self.sensor_data["folding_speed"] = max(3, min(20, self.sensor_data["folding_speed"]))

    def validate_process_data(self, process_data):
        """Validate folding process data"""
        required_fields = ["garment_to_fold", "fold_style"]
        return all(field in process_data for field in required_fields)
