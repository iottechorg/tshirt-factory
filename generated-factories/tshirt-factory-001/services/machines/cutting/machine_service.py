#!/usr/bin/env python3
"""
Machine Service Wrapper for cutting
Auto-generated service runner
"""
import sys
import os
import time
import logging
import threading

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../shared'))

from shared.mqtt_client import MQTTClientWrapper
from shared.database import DatabaseManager
from cutting_machine import CuttingMachine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MachineService:
    """Service wrapper for machine"""

    def __init__(self):
        self.machine_id = os.getenv('MACHINE_ID', 'cutting-01')
        self.machine_type = os.getenv('MACHINE_TYPE', 'cutting')
        self.factory_site_id = os.getenv('FACTORY_SITE_ID', 'site-01')

        # MQTT configuration
        self.mqtt_broker = os.getenv('MQTT_BROKER', 'localhost')
        self.mqtt_port = int(os.getenv('MQTT_PORT', 1883))

        # Initialize machine
        self.machine = CuttingMachine(
            machine_id=self.machine_id,
            machine_name=f"{self.machine_type}-{self.machine_id}"
        )

        # Initialize MQTT client
        self.mqtt_client = MQTTClientWrapper(
            client_id=f"{self.factory_site_id}-{self.machine_id}",
            broker=self.mqtt_broker,
            port=self.mqtt_port
        )

        # Topics
        self.telemetry_topic = f"factory/{self.factory_site_id}/machines/{self.machine_id}/telemetry"
        self.status_topic = f"factory/{self.factory_site_id}/machines/{self.machine_id}/status"
        self.command_topic = f"factory/{self.factory_site_id}/machines/{self.machine_id}/command"
        self.operation_topic = f"factory/{self.factory_site_id}/machines/{self.machine_id}/operation"

        self.running = False

    def on_command(self, topic, payload):
        """Handle incoming commands"""
        try:
            command = payload.get('command')
            logger.info(f"Received command: {command}")

            if command == 'start':
                self.machine.start()
            elif command == 'stop':
                self.machine.stop()
            elif command == 'set_failure_rate':
                rate = payload.get('rate', 0.01)
                self.machine.set_failure_rate(rate)

        except Exception as e:
            logger.error(f"Error handling command: {e}")

    def on_operation(self, topic, payload):
        """Handle operation requests"""
        try:
            logger.info(f"Processing operation: {payload}")
            result = self.machine.process_operation(payload)

            # Publish operation result
            result_topic = f"factory/{self.factory_site_id}/machines/{self.machine_id}/operation/result"
            self.mqtt_client.publish(result_topic, result)

        except Exception as e:
            logger.error(f"Error processing operation: {e}")

    def publish_telemetry(self):
        """Publish telemetry data periodically"""
        while self.running:
            try:
                # Update sensors
                self.machine.update_sensors()

                # Get telemetry
                telemetry = self.machine.get_telemetry()

                # Publish to MQTT
                self.mqtt_client.publish(self.telemetry_topic, telemetry)

                # Publish status
                status = self.machine.get_status()
                self.mqtt_client.publish(self.status_topic, status)

                # Sleep interval
                time.sleep(self.machine.telemetry_interval)

            except Exception as e:
                logger.error(f"Error publishing telemetry: {e}")
                time.sleep(5)

    def start(self):
        """Start the machine service"""
        logger.info(f"Starting machine service: {self.machine_id}")

        # Connect MQTT
        self.mqtt_client.connect()

        # Subscribe to topics
        self.mqtt_client.subscribe(self.command_topic, self.on_command)
        self.mqtt_client.subscribe(self.operation_topic, self.on_operation)

        # Start machine
        self.machine.start()
        self.running = True

        # Start telemetry thread
        telemetry_thread = threading.Thread(target=self.publish_telemetry, daemon=True)
        telemetry_thread.start()

        logger.info(f"Machine service started: {self.machine_id}")

        # Keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.stop()

    def stop(self):
        """Stop the machine service"""
        self.running = False
        self.machine.stop()
        self.mqtt_client.disconnect()
        logger.info("Machine service stopped")


if __name__ == "__main__":
    service = MachineService()
    service.start()
