"""
Template-Driven Test Case Generator - Generates test cases purely from machine templates.

This generator is FULLY generic - it makes NO assumptions about sensor names or types.
All test cases are derived from the machine template structure:
- Reads sensor definitions with min/max ranges
- Generates test cases that push sensors to extremes
- No hardcoded sensor names, types, or conditions

Usage:
    generator = TemplateDrivenTestGenerator(factory_config)
    test_cases = generator.generate_all_test_cases()
"""
import json
import random
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to machine templates directory
MACHINE_TEMPLATES_DIR = Path(__file__).parent.parent / "machine-templates"


class TemplateDrivenTestGenerator:
    """
    Generates test cases based purely on machine template specifications.
    
    Zero hardcoded assumptions about sensor names or factory types.
    Everything is derived from template JSON files.
    """
    
    def __init__(self, factory_config: Dict[str, Any]):
        """
        Initialize with factory configuration.
        
        Args:
            factory_config: Factory configuration dictionary
        """
        self.factory_config = factory_config
        self.factory_id = factory_config.get("factory_id", "unknown")
        self.machines = factory_config.get("machines", [])
        self.workflows = factory_config.get("workflows", [])
        
        # Load machine templates
        self.machine_templates = self._load_machine_templates()
        
        # Build machine-to-template mapping
        self.machine_sensor_specs = self._build_sensor_specifications()
        
        # Extract workflow parameters
        self.workflow_parameters = self._extract_workflow_parameters()
        
        # Extract product types
        self.product_types = list(set(
            w.get("product_type") or w.get("workflow_name")
            for w in self.workflows if w.get("product_type") or w.get("workflow_name")
        ))
        
        logger.info(f"TemplateDrivenTestGenerator initialized for {self.factory_id}")
        logger.info(f"  Machines: {len(self.machines)}")
        logger.info(f"  Machine types with templates: {len(self.machine_templates)}")
        logger.info(f"  Total sensors discovered: {sum(len(specs) for specs in self.machine_sensor_specs.values())}")
    
    def _load_machine_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load all machine templates from templates directory."""
        templates = {}
        
        templates_dir = MACHINE_TEMPLATES_DIR
        if not templates_dir.exists():
            logger.warning(f"Machine templates directory not found: {templates_dir}")
            return templates
        
        for template_file in templates_dir.glob("*.json"):
            try:
                with open(template_file) as f:
                    template = json.load(f)
                    machine_type = template.get("machine_type")
                    if machine_type:
                        templates[machine_type] = template
                        logger.debug(f"Loaded template: {machine_type}")
            except Exception as e:
                logger.error(f"Failed to load template {template_file}: {e}")
        
        return templates
    
    def _build_sensor_specifications(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Build sensor specifications for each machine instance.
        
        Returns:
            Dict mapping machine_id to list of sensor specifications
        """
        machine_sensors = {}
        
        for machine in self.machines:
            machine_id = machine.get("machine_id")
            machine_type = machine.get("machine_type")
            
            if not machine_id or not machine_type:
                continue
            
            # Get template for this machine type
            template = self.machine_templates.get(machine_type)
            if not template:
                logger.warning(f"No template found for machine type: {machine_type}")
                continue
            
            # Extract sensor specifications from template
            sensors = template.get("sensors", [])
            sensor_specs = []
            
            for sensor in sensors:
                sensor_name = sensor.get("name")
                sensor_range = sensor.get("range", {})
                
                # Only include sensors with numeric ranges
                if "min" in sensor_range and "max" in sensor_range:
                    sensor_specs.append({
                        "name": sensor_name,
                        "min": sensor_range["min"],
                        "max": sensor_range["max"],
                        "unit": sensor.get("unit", ""),
                        "type": sensor.get("type", "float")
                    })
            
            if sensor_specs:
                machine_sensors[machine_id] = sensor_specs
        
        return machine_sensors
    
    def _extract_workflow_parameters(self) -> Dict[str, List[Any]]:
        """Extract all parameters from workflow steps."""
        params_map = {}
        
        for workflow in self.workflows:
            for step in workflow.get("steps", []):
                step_params = step.get("parameters", {})
                for param_name, param_value in step_params.items():
                    if param_name not in params_map:
                        params_map[param_name] = set()
                    
                    if isinstance(param_value, dict) and "values" in param_value:
                        params_map[param_name].update(param_value["values"])
                    elif isinstance(param_value, (str, int, float)):
                        params_map[param_name].add(param_value)
        
        return {k: sorted(list(v), key=str) for k, v in params_map.items()}
    
    def generate_all_test_cases(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate comprehensive test cases based on machine templates.
        
        Returns:
            Dictionary mapping test categories to lists of test cases
        """
        test_cases = {
            "normal_operation": [],
            "sensor_extremes": [],
            "production_tests": []
        }
        
        # Normal operation tests
        test_cases["normal_operation"].append(self._generate_normal_test())
        
        # Sensor extreme tests - one for each sensor in each machine
        for machine_id, sensors in self.machine_sensor_specs.items():
            for sensor_spec in sensors:
                # Test at minimum value
                test_cases["sensor_extremes"].append(
                    self._generate_sensor_extreme_test(machine_id, sensor_spec, "min")
                )
                # Test at maximum value
                test_cases["sensor_extremes"].append(
                    self._generate_sensor_extreme_test(machine_id, sensor_spec, "max")
                )
        
        # Production request tests
        for _ in range(3):
            test_cases["production_tests"].append(self._generate_production_test())
        
        logger.info(f"Generated {sum(len(tests) for tests in test_cases.values())} test cases")
        return test_cases
    
    def _generate_normal_test(self) -> Dict[str, Any]:
        """Generate a normal operation test case."""
        return {
            "name": "normal_operation",
            "description": "Test factory under normal operating conditions",
            "category": "normal_operation",
            "steps": [self._generate_production_step()]
        }
    
    def _generate_sensor_extreme_test(
        self, 
        machine_id: str, 
        sensor_spec: Dict[str, Any], 
        extreme_type: str
    ) -> Dict[str, Any]:
        """
        Generate test case for sensor at extreme value.
        
        Args:
            machine_id: Machine to test
            sensor_spec: Sensor specification with min/max
            extreme_type: "min" or "max"
        """
        sensor_name = sensor_spec["name"]
        value = sensor_spec[extreme_type]
        unit = sensor_spec.get("unit", "")
        
        test_name = f"{machine_id}_{sensor_name}_{extreme_type}"
        description = f"Test {machine_id} with {sensor_name} at {extreme_type} value ({value} {unit})"
        
        return {
            "name": test_name,
            "description": description,
            "category": "sensor_extremes",
            "steps": [
                {
                    "action": "update_sensor",
                    "machine_id": machine_id,
                    "sensor_name": sensor_name,
                    "value": value
                },
                self._generate_production_step()
            ]
        }
    
    def _generate_production_test(self) -> Dict[str, Any]:
        """Generate a production request test case."""
        test_id = f"production_{random.randint(1000, 9999)}"
        
        return {
            "name": test_id,
            "description": "Random production request test",
            "category": "production_tests",
            "steps": [self._generate_production_step()]
        }
    
    def _generate_production_step(self) -> Dict[str, Any]:
        """Generate a production request step with factory-specific parameters."""
        product_type = random.choice(self.product_types) if self.product_types else "product"
        
        # Build product_details from workflow parameters
        product_details = {}
        for param_name, param_values in self.workflow_parameters.items():
            if param_values:
                product_details[param_name] = random.choice(param_values)
        
        # Add quantity if not present
        if "quantity" not in product_details:
            product_details["quantity"] = random.randint(1, 5)
        
        # Minimal fallback
        if not product_details or len(product_details) == 1:
            product_details.update({
                "quantity": random.randint(1, 5),
                "quality_tier": random.choice(["standard", "premium"])
            })
        
        return {
            "action": "production_request",
            "product_name": product_type,
            "product_details": product_details
        }
    
    def generate_sensor_coverage_report(self) -> Dict[str, Any]:
        """
        Generate a report showing sensor coverage across all machines.
        
        Returns:
            Dictionary with sensor statistics
        """
        total_machines = len(self.machines)
        machines_with_templates = len(self.machine_sensor_specs)
        total_sensors = sum(len(specs) for specs in self.machine_sensor_specs.values())
        
        sensor_names = set()
        for specs in self.machine_sensor_specs.values():
            for spec in specs:
                sensor_names.add(spec["name"])
        
        return {
            "factory_id": self.factory_id,
            "total_machines": total_machines,
            "machines_with_templates": machines_with_templates,
            "total_sensors": total_sensors,
            "unique_sensor_types": len(sensor_names),
            "sensor_types": sorted(list(sensor_names)),
            "test_cases_generated": {
                "normal_operation": 1,
                "sensor_extremes": total_sensors * 2,  # min and max for each
                "production_tests": 3,
                "total": 1 + (total_sensors * 2) + 3
            }
        }
