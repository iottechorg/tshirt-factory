"""
Cutting Machine Implementation
Auto-generated from template: machine-templates/cutting-machine.json
"""
import sys
import os
import random
import time
import math
from typing import Dict, Any

sys.path.insert(0, '/app/shared')

from base_machine import BaseMachine


class CuttingMachine(BaseMachine):
    """
    Fabric Cutting Machine - Industrial fabric cutting machine for t-shirt production

    Category: general

    Sensors:
    - blade_temperature: float (celsius)
    - blade_pressure: float (bar)
    - cut_speed: float (m/s)
    - motor_current: float (ampere)

    Operations:
    - cut_fabric: cut_fabric
    """

    def __init__(self, machine_id: str, machine_name: str = "cutting"):
        super().__init__(machine_id, "cutting", machine_name)
        self.operations = ["cut_fabric"]

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
              "blade_temperature": 30.0,
            "blade_pressure": 1.25,
            "cut_speed": 0.2,
            "motor_current": 0.85
        }

    def update_sensors(self):
        """Update sensor readings based on template behavior"""
        if not self.is_running:
            return

        self.sensor_data["blade_temperature"] += random.uniform(-0.5, 0.5)
        self.sensor_data["blade_temperature"] = max(20.0, min(45.0, self.sensor_data["blade_temperature"]))
        self.sensor_data["blade_pressure"] += random.uniform(-0.1, 0.1)
        self.sensor_data["blade_pressure"] = max(0.5, min(2.0, self.sensor_data["blade_pressure"]))
        self.sensor_data["cut_speed"] += random.uniform(-0.02, 0.02)
        self.sensor_data["cut_speed"] = max(0.05, min(0.5, self.sensor_data["cut_speed"]))
        self.sensor_data["motor_current"] += random.uniform(-0.2, 0.2)
        self.sensor_data["motor_current"] = max(0.3, min(1.5, self.sensor_data["motor_current"]))

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
                "name": "cut_fabric",
                "description": "Cut fabric according to pattern",
                "duration": {
                        "type": "fixed",
                        "value": 5.0
                },
                "inputs": [
                        {
                                "name": "material",
                                "type": "string",
                                "required": true,
                                "description": "Fabric material type"
                        },
                        {
                                "name": "cut_size",
                                "type": "string",
                                "required": true,
                                "description": "Size pattern (S, M, L, XL)"
                        }
                ],
                "outputs": [
                        {
                                "name": "cut_pieces",
                                "type": "object",
                                "description": "Cut fabric pieces ready for sewing"
                        }
                ],
                "failure_modes": [
                        {
                                "type": "random",
                                "probability": 0.02,
                                "condition": null,
                                "description": "Random cutting failure"
                        },
                        {
                                "type": "conditional",
                                "probability": 0.15,
                                "condition": "blade_temperature > 40",
                                "description": "High temperature causes poor cut quality"
                        }
                ],
                "sensor_impacts": [
                        {
                                "sensor": "blade_temperature",
                                "change": 2.0,
                                "duration": 10
                        },
                        {
                                "sensor": "motor_current",
                                "change": 0.3,
                                "duration": 5
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
