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
from factory_state_manager import FactoryStateManager
from mqtt_publisher import MQTTPublisher
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
    client_id=f"factory_ui_commands_{FACTORY_SITE_ID}",
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
    
    def request_production(self, product_name: str, product_details: dict = None):
        """Send production request to factory."""
        try:
            payload = {
                "product_name": product_name,
                "product_details": product_details or {}
            }
            self.publisher.publish(MQTT_TOPIC_PRODUCTION_REQUEST, json.dumps(payload))
            logger.info(f"Published production request: {product_name}")
        except Exception as e:
            logger.error(f"Error publishing production request: {e}")
    
    def update_sensor(self, machine_id: str, sensor_name: str, value: float):
        """Send sensor update to factory."""
        try:
            # Prefer per-machine command topic for machine-level updates
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
        
        # For now, just update local cache. In the future, publish to factory.
        # failure_rate would be handled by factory's production config update
        logger.info(f"Machine update requested for {machine_id}: {data}")
        return machine
    
    def update_machine_sensor(self, machine_id: str, sensor_name: str, value: float):
        """Update sensor value and send command to factory."""
        # Update local cache for immediate feedback
        machine = self.state_manager.update_sensor_cache(machine_id, sensor_name, value)
        if not machine:
            return None
        
        # Send command to factory
        self.command_mgr.update_sensor(machine_id, sensor_name, value)
        return machine


class ProductionManager:
    """Handle production requests via MQTT."""
    
    def __init__(self, command_mgr: CommandManager, state_mgr: FactoryStateManager):
        self.command_mgr = command_mgr
        self.state_mgr = state_mgr
    
    def request_production(self, product_name: str, product_details: dict = None):
        """Send production request to factory."""
        self.command_mgr.request_production(product_name, product_details)
    
    def get_production_status(self):
        """Get current production status from factory state."""
        return self.state_mgr.get_production_status()


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
        """Sequentially execute steps in a test case.

        Supported actions:
        - update_sensor: {machine_id, sensor_name, value}
        - production_request: {product_name, product_details}
        - update_failure_rate / update_production_success_rate: publish to config
        - run_custom_command: {machine_id, command, params}
        - wait/delay: {seconds}
        """
        try:
            name = test_case.get('name', '<unnamed>')
            logger.info(f"Executing test case: {name}")
            steps = test_case.get('steps', [])
            for step in steps:
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
                    if product_name:
                        self.command_mgr.request_production(product_name, product_details)

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
                        import time
                        logger.debug(f"Test '{name}' waiting for {seconds} seconds")
                        time.sleep(seconds)

                else:
                    logger.warning(f"Unknown test action: {action}")

            logger.info(f"Finished test case: {name}")
        except Exception as e:
            logger.exception(f"Error executing test case '{test_case.get('name', '<unnamed>')}': {e}")


# Global manager instances
command_manager = CommandManager(command_publisher)
machine_manager = MachineManager(factory_state_manager, command_manager)
production_manager = ProductionManager(command_manager, factory_state_manager)
test_manager = TestManager(command_manager)


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

