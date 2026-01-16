"""
Production Automation Controller - Manages automated random production generation
and test automation execution.
"""
import threading
import time
import json
import logging
import random
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AutomationState(Enum):
    """Automation execution states."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


class ProductionAutomation:
    """Manages automated production request generation with configurable frequency."""

    def __init__(self, production_request_callback: Callable, factory_config: Optional[Dict[str, Any]] = None):
        """
        Initialize production automation.

        Args:
            production_request_callback: Function to call for production requests
                                       signature: fn(product_name, product_details)
            factory_config: Factory configuration dict for extracting product parameters
        """
        self.production_request_callback = production_request_callback
        self.factory_config = factory_config or {}
        self.state = AutomationState.IDLE
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._config = {
            "interval_seconds": 5,
            "enabled": False,
            "total_requests": 0,
            "start_time": None
        }

        # Extract product parameters from factory config workflows
        self._extract_parameters()

    def start(self, interval_seconds: int = 5) -> Dict[str, Any]:
        """Start automated production."""
        if self.state == AutomationState.RUNNING:
            return {"status": "already_running", "message": "Automation already running"}

        self._config["interval_seconds"] = max(1, interval_seconds)
        self._config["enabled"] = True
        self._config["start_time"] = datetime.now().isoformat()
        self._config["total_requests"] = 0
        self.state = AutomationState.RUNNING
        self._stop_event.clear()

        self._thread = threading.Thread(target=self._run_automation, daemon=True)
        self._thread.start()

        logger.info(f"Started production automation with interval {interval_seconds}s")
        return {
            "status": "started",
            "message": "Production automation started",
            "interval_seconds": interval_seconds
        }

    def stop(self) -> Dict[str, Any]:
        """Stop automated production."""
        if self.state != AutomationState.RUNNING:
            return {"status": "not_running", "message": "Automation not running"}

        self._stop_event.set()
        self.state = AutomationState.STOPPED
        self._config["enabled"] = False

        if self._thread:
            self._thread.join(timeout=2)

        logger.info(f"Stopped production automation. Total requests: {self._config['total_requests']}")
        return {
            "status": "stopped",
            "message": "Production automation stopped",
            "total_requests": self._config["total_requests"]
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current automation status."""
        elapsed = None
        if self._config["start_time"]:
            try:
                start = datetime.fromisoformat(self._config["start_time"])
                elapsed = (datetime.now() - start).total_seconds()
            except:
                pass

        return {
            "state": self.state.value,
            "enabled": self._config["enabled"],
            "interval_seconds": self._config["interval_seconds"],
            "total_requests": self._config["total_requests"],
            "start_time": self._config["start_time"],
            "elapsed_seconds": elapsed
        }

    def _run_automation(self):
        """Run the automation loop."""
        try:
            while not self._stop_event.is_set():
                try:
                    # Generate random product
                    product_name, product_details = self._generate_random_product()

                    # Call production callback
                    self.production_request_callback(product_name, product_details)
                    self._config["total_requests"] += 1

                    logger.debug(f"Automation production request #{self._config['total_requests']}: {product_name}")

                    # Wait for next interval
                    self._stop_event.wait(self._config["interval_seconds"])

                except Exception as e:
                    logger.error(f"Error in automation loop: {e}")
                    # Continue on error
                    self._stop_event.wait(1)
        except Exception as e:
            logger.error(f"Automation thread fatal error: {e}")
            self.state = AutomationState.STOPPED

    def _extract_parameters(self):
        """Extract production parameters from factory workflows."""
        self.product_types = []
        self.workflow_parameters = {}

        workflows = self.factory_config.get("workflows", [])
        for workflow in workflows:
            # Extract product type
            product_type = workflow.get("product_type") or workflow.get("workflow_name")
            if product_type and product_type not in self.product_types:
                self.product_types.append(product_type)

            # Extract parameters from steps
            for step in workflow.get("steps", []):
                params = step.get("parameters", {})
                for param_name, param_value in params.items():
                    if param_name not in self.workflow_parameters:
                        self.workflow_parameters[param_name] = set()

                    # Handle different parameter value formats
                    if isinstance(param_value, dict) and "values" in param_value:
                        self.workflow_parameters[param_name].update(param_value["values"])
                    elif isinstance(param_value, (str, int, float)):
                        self.workflow_parameters[param_name].add(param_value)

        # Convert sets to lists
        self.workflow_parameters = {
            k: list(v) for k, v in self.workflow_parameters.items()
        }

        logger.debug(f"Extracted {len(self.product_types)} product types and {len(self.workflow_parameters)} parameter types")

    def _generate_random_product(self) -> tuple:
        """Generate random product name and details from factory workflows."""
        # Use extracted parameters or fallback to minimal defaults
        if self.product_types:
            product_name = random.choice(self.product_types)
        else:
            product_name = "product"

        product_details = {}

        # Build product_details from workflow parameters
        for param_name, param_values in self.workflow_parameters.items():
            if param_values:
                product_details[param_name] = random.choice(param_values)

        # Always add quantity
        if "quantity" not in product_details:
            product_details["quantity"] = random.randint(1, 5)

        # Minimal fallback if no parameters extracted
        if not product_details or len(product_details) == 1:  # only quantity
            product_details.update({
                "quantity": random.randint(1, 5),
                "quality_tier": random.choice(["standard", "premium"])
            })

        return product_name, product_details


class TestAutomation:
    """Manages automated test case execution."""

    def __init__(self, test_execution_callback: Callable):
        """
        Initialize test automation.

        Args:
            test_execution_callback: Function to call for test execution
                                    signature: fn(test_case: dict)
        """
        self.test_execution_callback = test_execution_callback
        self.state = AutomationState.IDLE
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._config = {
            "interval_seconds": 30,
            "enabled": False,
            "total_tests": 0,
            "test_cases": [],
            "start_time": None
        }

    def start(self, test_cases: list, interval_seconds: int = 30) -> Dict[str, Any]:
        """Start automated test execution."""
        if self.state == AutomationState.RUNNING:
            return {"status": "already_running", "message": "Test automation already running"}

        if not test_cases:
            return {"status": "error", "message": "No test cases provided"}

        self._config["interval_seconds"] = max(5, interval_seconds)
        self._config["test_cases"] = test_cases
        self._config["enabled"] = True
        self._config["start_time"] = datetime.now().isoformat()
        self._config["total_tests"] = 0
        self.state = AutomationState.RUNNING
        self._stop_event.clear()

        self._thread = threading.Thread(target=self._run_automation, daemon=True)
        self._thread.start()

        logger.info(f"Started test automation with {len(test_cases)} test cases, interval {interval_seconds}s")
        return {
            "status": "started",
            "message": "Test automation started",
            "test_count": len(test_cases),
            "interval_seconds": interval_seconds
        }

    def stop(self) -> Dict[str, Any]:
        """Stop automated test execution."""
        if self.state != AutomationState.RUNNING:
            return {"status": "not_running", "message": "Test automation not running"}

        self._stop_event.set()
        self.state = AutomationState.STOPPED
        self._config["enabled"] = False

        if self._thread:
            self._thread.join(timeout=2)

        logger.info(f"Stopped test automation. Total tests: {self._config['total_tests']}")
        return {
            "status": "stopped",
            "message": "Test automation stopped",
            "total_tests": self._config["total_tests"]
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current test automation status."""
        elapsed = None
        if self._config["start_time"]:
            try:
                start = datetime.fromisoformat(self._config["start_time"])
                elapsed = (datetime.now() - start).total_seconds()
            except:
                pass

        return {
            "state": self.state.value,
            "enabled": self._config["enabled"],
            "interval_seconds": self._config["interval_seconds"],
            "total_tests": self._config["total_tests"],
            "test_count": len(self._config["test_cases"]),
            "start_time": self._config["start_time"],
            "elapsed_seconds": elapsed
        }

    def _run_automation(self):
        """Run the automation loop."""
        try:
            test_index = 0
            while not self._stop_event.is_set():
                try:
                    if test_index >= len(self._config["test_cases"]):
                        test_index = 0  # Loop back to beginning

                    test_case = self._config["test_cases"][test_index]

                    # Execute test
                    self.test_execution_callback(test_case)
                    self._config["total_tests"] += 1
                    test_index += 1

                    logger.debug(f"Automation test #{self._config['total_tests']}: {test_case.get('name')}")

                    # Wait for next interval
                    self._stop_event.wait(self._config["interval_seconds"])

                except Exception as e:
                    logger.error(f"Error in test automation loop: {e}")
                    self._stop_event.wait(1)
        except Exception as e:
            logger.error(f"Test automation thread fatal error: {e}")
            self.state = AutomationState.STOPPED