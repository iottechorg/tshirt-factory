"""
Simplified Factory Manager

No longer manages local machine/production simulation.
Now acts as a MQTT-based state manager that:
1. Listens for factory status updates via MQTT
2. Publishes commands (sensor updates, production requests, tests) to the factory
3. Provides state query methods for REST endpoints
"""

import logging
import threading
import time
from factory_state_manager import FactoryStateManager
from mqtt_publisher import MQTTPublisher
import sys
from pathlib import Path
import json
import os

logger = logging.getLogger(__name__)

# Factory config will be loaded lazily
_factory_config = None

def _get_factory_config():
    """Get factory configuration for automation (lazy loading)."""
    global _factory_config
    if _factory_config is None:
        try:
            # Get factory site ID from environment
            factory_site_id = os.getenv("FACTORY_SITE_ID", "tshirt-factory-001")
            
            # Try to load from generated factories directory
            config_path = Path(__file__).parent.parent / "generated-factories" / factory_site_id / "factory-config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    _factory_config = json.load(f)
                    logger.info(f"Loaded factory config from {config_path}")
                    return _factory_config
            
            # Fallback: try main factory configs
            config_path = Path(__file__).parent.parent / "factory-configs" / f"{factory_site_id}.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    _factory_config = json.load(f)
                    logger.info(f"Loaded factory config from {config_path}")
                    return _factory_config
                    
            logger.warning("Could not find factory config file")
            _factory_config = {}
        except Exception as e:
            logger.error(f"Error loading factory config: {e}")
            _factory_config = {}
    
    return _factory_config

# Import config after lazy loading is set up
# Define config variables directly to avoid import issues
MQTT_BROKER = os.getenv("MQTT_BROKER", "tshirt-factory-001-mqtt")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
FACTORY_SITE_ID = os.getenv("FACTORY_SITE_ID", "tshirt-factory-001")
MQTT_TOPIC_PRODUCTION_REQUEST = f"factory/{FACTORY_SITE_ID}/production/request"
MQTT_TOPIC_SENSOR_UPDATE = f"factory/{FACTORY_SITE_ID}/sensor/update"
MQTT_TOPIC_TEST_REQUEST = f"factory/{FACTORY_SITE_ID}/test/request"
MQTT_TOPIC_CONFIG = f"factory/{FACTORY_SITE_ID}/config"

try:
    from production_automation import ProductionAutomation, TestAutomation
    _PROD_AUTOMATION_AVAILABLE = True
except Exception as _e:
    print(f"WARNING: production_automation not importable: {_e}")
    _PROD_AUTOMATION_AVAILABLE = False

    class ProductionAutomation:
        """Fallback ProductionAutomation stub when real module is unavailable."""
        def __init__(self, callback=None, factory_config=None):
            class _State:
                value = "stopped"
            self.state = _State()

        def start(self, interval_seconds: int = 5):
            logger.warning("ProductionAutomation.start() called but production_automation module is missing")
            return {"status": "not_available", "message": "production_automation_not_available"}

        def stop(self):
            logger.warning("ProductionAutomation.stop() called but production_automation module is missing")
            return {"status": "not_available", "message": "production_automation_not_available"}

        def get_status(self):
            return {"state": "not_available"}

    class TestAutomation:
        """Fallback TestAutomation stub when real module is unavailable."""
        def __init__(self, callback=None):
            class _State:
                value = "stopped"
            self.state = _State()

        def start(self, *args, **kwargs):
            logger.warning("TestAutomation.start() called but production_automation module is missing")
            return {"status": "not_available"}

        def stop(self, *args, **kwargs):
            logger.warning("TestAutomation.stop() called but production_automation module is missing")
            return {"status": "not_available"}

        def get_status(self):
            return {"state": "not_available"}
from config import (
    MQTT_BROKER, MQTT_PORT, FACTORY_SITE_ID,
    MQTT_TOPIC_PRODUCTION_REQUEST, MQTT_TOPIC_SENSOR_UPDATE, MQTT_TOPIC_TEST_REQUEST,
    MQTT_TOPIC_CONFIG
)
import json

logger = logging.getLogger(__name__)

# Global state manager and publishers
factory_state_manager = FactoryStateManager(
    mqtt_broker=MQTT_BROKER,
    mqtt_port=MQTT_PORT,
    factory_site_id=FACTORY_SITE_ID
)

# MQTT publisher for sending commands to factory
command_publisher = MQTTPublisher(
    client_id=f"factory_ui_commands_{FACTORY_SITE_ID}_{int(__import__('time').time())}",
    enable_logs=True
)


class CommandManager:
    """Manages sending commands to the factory via MQTT."""
    
    def __init__(self, publisher: MQTTPublisher):
        self.publisher = publisher
        self.is_connected = False
    
    def connect(self):
        """Connect publisher."""
        try:
            self.publisher.connect()
            self.publisher.loop_start()
            self.is_connected = True
            logger.info("CommandManager connected")
        except Exception as e:
            logger.error(f"Failed to connect CommandManager: {e}")
    
    def stop(self):
        """Stop publisher."""
        if self.is_connected:
            self.publisher.loop_stop()
            logger.info("CommandManager stopped")
    
    def request_production(self, product_name: str, product_details: dict = None, workflow_id: str = None, quantity: int = 1):
        """Send production request(s) to factory.
        
        For scalability, publishes individual production requests for each item.
        This allows the factory orchestrator to queue and process them independently.
        
        Args:
            product_name: Name of the product to produce
            product_details: Additional product details
            workflow_id: Optional workflow ID
            quantity: Number of items to produce (default: 1)
        """
        try:
            # Validate and clamp quantity
            quantity = max(1, min(100, int(quantity)))
            
            # Publish individual production requests for scalability
            # Each request can be tracked and processed independently by the factory
            for i in range(quantity):
                payload = {
                    "product_name": product_name,
                    "product_details": product_details or {}
                }
                if workflow_id:
                    payload["workflow_id"] = workflow_id
                
                # Add batch metadata for tracking
                if quantity > 1:
                    payload["batch_info"] = {
                        "item_number": i + 1,
                        "total_items": quantity
                    }
                
                self.publisher.publish(MQTT_TOPIC_PRODUCTION_REQUEST, json.dumps(payload))
            
            logger.info(
                f"Published {quantity} production request(s): {product_name} "
                f"(workflow: {workflow_id or 'default'})"
            )
        except Exception as e:
            logger.error(f"Error publishing production request: {e}")
    
    def update_sensor(self, machine_id: str, sensor_name: str, value: float):
        """Send sensor update to factory."""
        try:
            # Prefer machine-type-aware command topic when available. If caller provides
            # a machine_type via kwargs, use the canonical topic; otherwise fall back
            # to the legacy plural 'machines' topic for backwards compatibility.
            machine_type = None
            # allow callers to pass machine_type via attribute if set
            if hasattr(self, 'last_machine_type') and self.last_machine_type:
                machine_type = self.last_machine_type

            if machine_type:
                topic = f"factory/{FACTORY_SITE_ID}/machine/{machine_type}/{machine_id}/command"
            else:
                topic = f"factory/{FACTORY_SITE_ID}/machines/{machine_id}/command"

            cmd = {"command": "update_sensor", "sensor_name": sensor_name, "value": float(value)}
            self.publisher.publish(topic, json.dumps(cmd))
            logger.info(f"Published sensor update: {machine_id}/{sensor_name}={value} to {topic}")
        except Exception as e:
            logger.error(f"Error publishing sensor update: {e}")

    def send_machine_command(self, machine_id: str, command: str, params: dict = None):
        """Publish an arbitrary command to a specific machine's command topic."""
        try:
            topic = f"factory/{FACTORY_SITE_ID}/machines/{machine_id}/command"
            payload = {"command": command}
            if params:
                payload.update(params)
            self.publisher.publish(topic, json.dumps(payload))
            logger.info(f"Published command '{command}' to {machine_id} on {topic}")
        except Exception as e:
            logger.error(f"Error publishing machine command: {e}")
    
    def run_test_case(self, test_case: dict):
        """Send test case to factory for execution."""
        try:
            self.publisher.publish(MQTT_TOPIC_TEST_REQUEST, json.dumps(test_case))
            logger.info(f"Published test case: {test_case.get('name', 'unknown')}")
        except Exception as e:
            logger.error(f"Error publishing test case: {e}")


class MachineManager:
    """Query machines from factory state and send updates."""
    
    def __init__(self, state_manager: FactoryStateManager, command_mgr: CommandManager):
        self.state_manager = state_manager
        self.command_mgr = command_mgr
    
    def get_machines(self):
        """Get current machines from factory state."""
        return self.state_manager.get_machines()
    
    def update_machine(self, machine_id: str, data: dict):
        """
        Update machine settings (e.g., failure_rate).
        Currently supports: failure_rate
        """
        machine = self.state_manager.get_machine(machine_id)
        if not machine:
            logger.warning(f"Machine {machine_id} not found")
            return None
        
        # Publish to machine-specific config topic
        if 'failure_rate' in data:
            try:
                # 1. Publish to config topic
                topic = f"factory/{FACTORY_SITE_ID}/machines/{machine_id}/config"
                payload = json.dumps({"failure_rate": float(data['failure_rate'])})
                self.command_mgr.publisher.publish(topic, payload)
                
                # 2. ALSO publish to command topic for backward compatibility with machine services
                cmd_topic = f"factory/{FACTORY_SITE_ID}/machines/{machine_id}/command"
                cmd_payload = json.dumps({
                    "command": "set_failure_rate",
                    "rate": float(data['failure_rate'])
                })
                self.command_mgr.publisher.publish(cmd_topic, cmd_payload)
                
                logger.info(f"Published machine config update for {machine_id}: {payload} to {topic} and {cmd_topic}")
            except Exception as e:
                logger.error(f"Failed to publish machine config for {machine_id}: {e}")
        
        return machine
    
    def update_machine_sensor(self, machine_id: str, sensor_name: str, value: float):
        """Update sensor value and send command to factory."""
        # Update local cache for immediate feedback
        machine = self.state_manager.update_sensor_cache(machine_id, sensor_name, value)
        if not machine:
            return None
        
        # Send command to factory. If we have a machine_type in the cached state,
        # set it on the command manager so it will publish to the canonical
        # machine-specific topic (factory/{site}/machine/{type}/{id}/command).
        try:
            machine_type = machine.get('machine_type')
            if machine_type:
                # Store temporarily on the command manager instance
                setattr(self.command_mgr, 'last_machine_type', machine_type)
        except Exception:
            pass

        self.command_mgr.update_sensor(machine_id, sensor_name, value)
        # Clear the temporary attribute to avoid leaking state
        try:
            if hasattr(self.command_mgr, 'last_machine_type'):
                delattr(self.command_mgr, 'last_machine_type')
        except Exception:
            pass
        return machine


class ProductionManager:
    """Handle production requests via MQTT."""
    
    def __init__(self, command_mgr: CommandManager, state_mgr: FactoryStateManager):
        self.command_mgr = command_mgr
        self.state_mgr = state_mgr
        self._production_history = []
    
    def request_production(self, product_name: str, product_details: dict = None, workflow_id: str = None, quantity: int = 1):
        """Send production request(s) to factory.
        
        Args:
            product_name: Name of the product to produce
            product_details: Additional product details
            workflow_id: Optional workflow ID
            quantity: Number of items to produce (default: 1)
        """
        self.command_mgr.request_production(product_name, product_details, workflow_id, quantity)
    
    def get_production_status(self):
        """Get current production status from factory state."""
        return self.state_mgr.get_production_status()

    def update_production_config(self, config_data: dict):
        """Update global production configuration via MQTT."""
        try:
            payload = json.dumps({"production": config_data})
            self.command_mgr.publisher.publish(MQTT_TOPIC_CONFIG, payload)
            logger.info(f"Published global production config: {payload}")
            return True
        except Exception as e:
            logger.error(f"Error publishing production config: {e}")
            return False
    
    def clear_production_history(self):
        """Clear production history."""
        self._production_history = []
        logger.info("Production history cleared")
        return True


class TestManager:
    """Handle test case execution."""
    
    def __init__(self, command_mgr: CommandManager):
        self.command_mgr = command_mgr
        self._running_threads = []

    def run_test_case(self, test_case: dict):
        """Execute the provided test case asynchronously."""
        try:
            t = threading.Thread(target=self._execute_test_case, args=(test_case,), daemon=True)
            t.start()
            self._running_threads.append(t)
            logger.info(f"Started test case execution: {test_case.get('name', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to start test case thread: {e}")

    def _execute_test_case(self, test_case: dict):
        """Sequentially execute steps in a test case."""
        import time
        name = test_case.get('name', '<unnamed>')
        try:
            logger.info(f"Executing test case: {name}")
            steps = test_case.get('steps', [])
            total_steps = len(steps)
            
            # Setup notification topic
            status_topic = f"factory/{FACTORY_SITE_ID}/test/status"
            
            for i, step in enumerate(steps):
                # Publish progress
                progress = {
                    "test_name": name,
                    "step_index": i,
                    "total_steps": total_steps,
                    "action": step.get('action'),
                    "status": "running",
                    "timestamp": time.time()
                }
                self.command_mgr.publisher.publish(status_topic, json.dumps(progress))

                action = (step.get('action') or '').lower()
                if not action:
                    continue

                if action in ('update_sensor', 'update_sensor_value'):
                    machine_id = step.get('machine_id') or step.get('machine') or step.get('machine_name')
                    sensor = step.get('sensor_name') or step.get('sensor')
                    value = step.get('value')
                    if machine_id and sensor and value is not None:
                        self.command_mgr.send_machine_command(machine_id, 'update_sensor', {'sensor_name': sensor, 'value': value})

                elif action in ('production_request', 'production'):
                    product_name = step.get('product_name') or step.get('product_type') or step.get('product')
                    product_details = step.get('product_details') or step.get('details') or {}
                    quantity = step.get('quantity', 1)  # Support quantity in automation steps
                    if product_name:
                        self.command_mgr.request_production(product_name, product_details, None, quantity)

                elif action in ('update_failure_rate', 'set_failure_rate'):
                    rate = step.get('rate') or step.get('failure_rate')
                    if rate is not None:
                        try:
                            payload = json.dumps({"production": {"failure_rate": float(rate)}})
                            self.command_mgr.publisher.publish(MQTT_TOPIC_CONFIG, payload)
                            logger.info(f"Published failure_rate config: {rate}")
                        except Exception as e:
                            logger.error(f"Failed to publish failure_rate config: {e}")

                elif action == 'update_production_success_rate':
                    success_rate = step.get('success_rate')
                    if success_rate is not None:
                        try:
                            payload = json.dumps({"production": {"success_rate": float(success_rate)}})
                            self.command_mgr.publisher.publish(MQTT_TOPIC_CONFIG, payload)
                            logger.info(f"Published success_rate config: {success_rate}")
                        except Exception as e:
                            logger.error(f"Failed to publish success_rate config: {e}")

                elif action in ('run_custom_command', 'custom_command'):
                    machine_id = step.get('machine_id')
                    cmd = step.get('command')
                    params = step.get('params') or step.get('payload')
                    if machine_id and cmd:
                        self.command_mgr.send_machine_command(machine_id, cmd, params)

                elif action in ('wait', 'delay', 'sleep'):
                    seconds = float(step.get('seconds', 0) or step.get('delay', 0))
                    if seconds > 0:
                        logger.debug(f"Test '{name}' waiting for {seconds} seconds")
                        time.sleep(seconds)

                else:
                    logger.warning(f"Unknown test action: {action}")
            
            # Publish completion
            completion = {
                "test_name": name,
                "status": "completed",
                "timestamp": time.time()
            }
            self.command_mgr.publisher.publish(status_topic, json.dumps(completion))
            logger.info(f"Finished test case: {name}")
        except Exception as e:
            logger.exception(f"Error executing test case '{name}': {e}")
            # Notify error
            try:
                error_status = {
                    "test_name": name,
                    "status": "error",
                    "error": str(e),
                    "timestamp": time.time()
                }
                self.command_mgr.publisher.publish(f"factory/{FACTORY_SITE_ID}/test/status", json.dumps(error_status))
            except:
                pass


# Callbacks for automation
def _production_automation_callback(product_name, product_details):
    """Callback for production automation."""
    # For automation, we don't want to actually send production requests to the factory
    # as they would show up on the UI. Instead, just log the automated request.
    logger.info(f"🔄 Automated production request: {product_name} with details: {product_details}")
    # Note: We intentionally do NOT call command_manager.request_production() here
    # to prevent automated requests from appearing on the production page

def _test_automation_callback(test_case):
    """Callback for test automation."""
    # Get test_manager reference (will be set after managers are created)
    if hasattr(_test_automation_callback, '_test_manager'):
        _test_automation_callback._test_manager.run_test_case(test_case)


# Global manager instances
command_manager = CommandManager(command_publisher)
machine_manager = MachineManager(factory_state_manager, command_manager)
production_manager = ProductionManager(command_manager, factory_state_manager)
test_manager = TestManager(command_manager)

# Automation managers
production_automation = ProductionAutomation(_production_automation_callback, _get_factory_config())
test_automation = TestAutomation(_test_automation_callback)

# Set references for callbacks
_production_automation_callback._command_manager = command_manager
_test_automation_callback._test_manager = test_manager


def initialize_managers():
    """Initialize all managers and connect to MQTT."""
    try:
        logger.info("Initializing factory managers...")
        factory_state_manager.connect()
        command_manager.connect()
        logger.info("Factory managers initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize managers: {e}")
        raise


def stop_managers():
    """Stop all managers."""
    try:
        command_manager.stop()
        factory_state_manager.stop()
        logger.info("Factory managers stopped")
    except Exception as e:
        logger.error(f"Error stopping managers: {e}")

