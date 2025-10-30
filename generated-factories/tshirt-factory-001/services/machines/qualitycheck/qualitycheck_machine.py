"""
Qualitycheck Machine Implementation
Auto-generated from template: machine-templates/quality-check-machine.json
"""
import sys
import os
import random
import time
import math
from typing import Dict, Any

sys.path.insert(0, '/app/shared')

from base_machine import BaseMachine


class QualitycheckMachine(BaseMachine):
    """
    Automated Quality Inspection System - AI-powered vision inspection system for t-shirt quality control

    Category: general

    Sensors:
    - camera_temperature: float (celsius)
    - light_intensity: float (lux)
    - scan_speed: float (items/s)
    - defect_detection_rate: float (percentage)
    - inspection_score: float (score)

    Operations:
    - inspect_quality: inspect_quality
    - detailed_inspection: detailed_inspection
    """

    def __init__(self, machine_id: str, machine_name: str = "qualitycheck"):
        super().__init__(machine_id, "qualitycheck", machine_name)
        self.operations = ["inspect_quality", "detailed_inspection"]

        # Template metadata
        self.template_info = {
            "manufacturer": "Unknown",
            "model": "N/A",
            "category": "general"
        }

        # Telemetry configuration
        self.telemetry_interval = 5.0
        self.sensor_update_interval = 1.0

        # Initialize custom metrics
        self.custom_metrics = {}

    def _initialize_sensors(self) -> Dict[str, Any]:
        """Initialize sensor values from template"""
        return {
              "camera_temperature": 30.0,
            "light_intensity": 1000.0,
            "scan_speed": 1.0,
            "defect_detection_rate": 0.97,
            "inspection_score": 95.0
        }

    def update_sensors(self):
        """Update sensor readings based on template behavior"""
        if not self.is_running:
            return

        self.sensor_data["camera_temperature"] += random.uniform(-0.5, 0.5)
        self.sensor_data["camera_temperature"] = max(20.0, min(40.0, self.sensor_data["camera_temperature"]))
        self.sensor_data["light_intensity"] += random.uniform(-20.0, 20.0)
        self.sensor_data["light_intensity"] = max(750.0, min(1250.0, self.sensor_data["light_intensity"]))
        self.sensor_data["scan_speed"] += random.uniform(-0.1, 0.1)
        self.sensor_data["scan_speed"] = max(0.3, min(2.0, self.sensor_data["scan_speed"]))
        self.sensor_data["defect_detection_rate"] += random.uniform(-0.005, 0.005)
        self.sensor_data["defect_detection_rate"] = max(0.92, min(0.995, self.sensor_data["defect_detection_rate"]))
        self.sensor_data["inspection_score"] += random.uniform(-3.0, 3.0)
        self.sensor_data["inspection_score"] = max(0.0, min(100.0, self.sensor_data["inspection_score"]))

    def validate_process_data(self, process_data: Dict) -> bool:
        """Validate process data based on operation requirements"""
        if not isinstance(process_data, dict):
            return False

        operation = process_data.get("operation")
        if operation not in self.operations:
            return False

        # Get operation template
        op_template = self._get_operation_template(operation)
        if not op_template:
            return True  # No template validation

        # Validate required inputs
        required_inputs = [inp['name'] for inp in op_template.get('inputs', []) if inp.get('required', True)]
        return all(inp in process_data for inp in required_inputs)

    def _get_operation_template(self, operation_name: str) -> Dict:
        """Get operation configuration from template"""
        operations_templates = [
        {
                "name": "inspect_quality",
                "description": "Perform automated quality inspection",
                "duration": {
                        "type": "fixed",
                        "value": 3.0
                },
                "inputs": [
                        {
                                "name": "sewn_tshirt",
                                "type": "object",
                                "required": true,
                                "description": "Sewn t-shirt from sewing machine"
                        }
                ],
                "outputs": [
                        {
                                "name": "inspected_tshirt",
                                "type": "object",
                                "description": "Quality-approved t-shirt"
                        },
                        {
                                "name": "quality_report",
                                "type": "object",
                                "description": "Detailed inspection report"
                        }
                ],
                "failure_modes": [
                        {
                                "type": "random",
                                "probability": 0.05,
                                "condition": null,
                                "description": "Random quality failure"
                        },
                        {
                                "type": "conditional",
                                "probability": 0.3,
                                "condition": "light_intensity < 850",
                                "description": "Poor lighting causes inspection errors"
                        },
                        {
                                "type": "conditional",
                                "probability": 0.2,
                                "condition": "inspection_score < 80",
                                "description": "Low quality score triggers rejection"
                        }
                ],
                "sensor_impacts": [
                        {
                                "sensor": "camera_temperature",
                                "change": 1.5,
                                "duration": 3
                        },
                        {
                                "sensor": "inspection_score",
                                "change": -2.0,
                                "duration": 1
                        }
                ]
        },
        {
                "name": "detailed_inspection",
                "description": "Perform detailed manual-assisted inspection",
                "duration": {
                        "type": "fixed",
                        "value": 10.0
                },
                "inputs": [
                        {
                                "name": "sewn_tshirt",
                                "type": "object",
                                "required": true,
                                "description": "T-shirt requiring detailed inspection"
                        }
                ],
                "outputs": [
                        {
                                "name": "inspected_tshirt",
                                "type": "object",
                                "description": "Fully inspected t-shirt"
                        },
                        {
                                "name": "detailed_report",
                                "type": "object",
                                "description": "Comprehensive quality report"
                        }
                ],
                "failure_modes": [
                        {
                                "type": "random",
                                "probability": 0.01,
                                "condition": null,
                                "description": "Rare detailed inspection failure"
                        }
                ]
        }
]
        for op in operations_templates:
            if op['name'] == operation_name:
                return op
        return {}

    def calculate_custom_metrics(self) -> Dict[str, float]:
        """Calculate custom metrics defined in template"""
        metrics = {}

        # Add template-defined metrics here
        # Example: "weld_quality_index": "(arc_voltage - 20) / 10 * 100"

        return metrics

    def process_operation(self, process_data: Dict) -> Dict:
        """Process an operation based on template configuration"""
        if not self.validate_process_data(process_data):
            return {
                "status": "failed",
                "error": "Invalid process data",
                "machine_id": self.machine_id,
                "machine_type": self.machine_type
            }

        operation = process_data.get("operation")
        op_template = self._get_operation_template(operation)

        # Calculate duration
        duration = self._calculate_duration(op_template, process_data)

        # Simulate processing
        time.sleep(min(duration, 2.0))  # Cap at 2 seconds for simulation

        # Check for failures
        if self._check_failures(op_template):
            return {
                "status": "failed",
                "error": "Operation failed",
                "machine_id": self.machine_id,
                "machine_type": self.machine_type,
                "operation": operation
            }

        # Apply sensor impacts
        self._apply_sensor_impacts(op_template)

        return {
            "status": "success",
            "machine_id": self.machine_id,
            "machine_type": self.machine_type,
            "operation": operation,
            "outputs": op_template.get('outputs', []),
            "duration": duration,
            "timestamp": time.time()
        }

    def _calculate_duration(self, op_template: Dict, process_data: Dict) -> float:
        """Calculate operation duration from template"""
        if not op_template:
            return 1.0

        duration_config = op_template.get('duration', {})
        duration_type = duration_config.get('type', 'fixed')

        if duration_type == 'fixed':
            return duration_config.get('value', 1.0)
        elif duration_type == 'range':
            return random.uniform(
                duration_config.get('min', 1.0),
                duration_config.get('max', 5.0)
            )
        elif duration_type == 'formula':
            # TODO: Safely evaluate formula
            return duration_config.get('value', 1.0)

        return 1.0

    def _check_failures(self, op_template: Dict) -> bool:
        """Check if operation should fail based on template failure modes"""
        if not op_template:
            return self.simulate_failure()

        failure_modes = op_template.get('failure_modes', [])
        for failure_mode in failure_modes:
            probability = failure_mode.get('probability', 0.01)
            if random.random() < probability:
                # Check conditions if any
                conditions = failure_mode.get('conditions', {})
                if self._check_failure_conditions(conditions):
                    return True

        return False

    def _check_failure_conditions(self, conditions: Dict) -> bool:
        """Check if failure conditions are met"""
        for sensor_name, condition in conditions.items():
            if sensor_name not in self.sensor_data:
                continue

            value = self.sensor_data[sensor_name]
            if 'min' in condition and value < condition['min']:
                return True
            if 'max' in condition and value > condition['max']:
                return True

        return False

    def _apply_sensor_impacts(self, op_template: Dict):
        """Apply sensor impacts from operation"""
        sensor_impacts = op_template.get('sensor_impacts', [])
        for impact in sensor_impacts:
            sensor_name = impact['sensor_name']
            if sensor_name in self.sensor_data:
                change = impact['impact'].get('change')
                if change is not None:
                    if isinstance(change, bool):
                        self.sensor_data[sensor_name] = change
                    else:
                        self.sensor_data[sensor_name] += change
