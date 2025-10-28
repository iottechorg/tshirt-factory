"""
Folding Machine Service - Main Entry Point
"""
import sys
import os
import time
import logging
import signal
import json

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../shared'))

from folding_machine import FoldingMachine
from mqtt_client import MQTTClient
from config import (
    MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE,
    MACHINE_ID, MACHINE_SENSOR_UPDATE_INTERVAL,
    MACHINE_DATA_PUBLISH_INTERVAL,
    get_machine_status_topic, get_machine_telemetry_topic,
    get_machine_command_topic
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
machine = None
mqtt_client = None
running = True


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    global running
    logger.info("Shutdown signal received, stopping machine service...")
    running = False


def handle_command(topic, payload):
    """Handle incoming MQTT commands"""
    global machine
    try:
        command = json.loads(payload)
        command_type = command.get("command")

        logger.info(f"Received command: {command_type}")

        if command_type == "update_sensor":
            sensor_name = command.get("sensor_name")
            value = command.get("value")
            if sensor_name and value is not None:
                machine.update_sensor_value(sensor_name, value)
                logger.info(f"Updated sensor {sensor_name} to {value}")

        elif command_type == "set_failure_rate":
            rate = command.get("rate")
            if rate is not None:
                machine.set_failure_rate(float(rate))
                logger.info(f"Updated failure rate to {rate}")

        elif command_type == "process":
            process_data = command.get("process_data")
            if process_data:
                result = machine.process_operation(process_data)
                logger.info(f"Process result: {result['status']}")
                # Publish result back (could be to a different topic)
                response_topic = command.get("response_topic")
                if response_topic:
                    mqtt_client.publish_json(response_topic, result)

        elif command_type == "stop":
            machine.stop()
            logger.info("Machine stopped")

        elif command_type == "start":
            machine.start()
            logger.info("Machine started")

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in command: {e}")
    except Exception as e:
        logger.error(f"Error handling command: {e}")


def publish_status():
    """Publish machine status"""
    status_topic = get_machine_status_topic("folding", machine.machine_id)
    status = machine.get_status()
    mqtt_client.publish_json(status_topic, status)


def publish_telemetry():
    """Publish machine telemetry"""
    telemetry_topic = get_machine_telemetry_topic("folding", machine.machine_id)
    telemetry = machine.get_telemetry()
    mqtt_client.publish_json(telemetry_topic, telemetry)


def main():
    """Main service loop"""
    global machine, mqtt_client, running

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Get machine ID from environment or generate one
    machine_id = MACHINE_ID or f"folding-{int(time.time())}"
    logger.info(f"Starting Folding Machine Service: {machine_id}")

    # Initialize machine
    machine = FoldingMachine(machine_id)
    machine.start()

    # Initialize MQTT client
    mqtt_client = MQTTClient(
        client_id=f"folding-machine-{machine_id}",
        broker=MQTT_BROKER,
        port=MQTT_PORT,
        keepalive=MQTT_KEEPALIVE
    )

    # Connect to MQTT broker
    if not mqtt_client.connect():
        logger.error("Failed to connect to MQTT broker, exiting...")
        return

    # Subscribe to command topic
    command_topic = get_machine_command_topic("folding", machine_id)
    mqtt_client.subscribe(command_topic, handle_command)

    # Start MQTT loop
    mqtt_client.loop_start()

    logger.info(f"Folding machine {machine_id} is running...")
    logger.info(f"Listening for commands on: {command_topic}")

    last_telemetry_time = time.time()
    last_status_time = time.time()

    # Main loop
    try:
        while running:
            current_time = time.time()

            # Update sensors
            if machine.is_running:
                machine.update_sensors()

            # Publish telemetry at regular intervals
            if current_time - last_telemetry_time >= MACHINE_DATA_PUBLISH_INTERVAL:
                publish_telemetry()
                last_telemetry_time = current_time

            # Publish status less frequently
            if current_time - last_status_time >= MACHINE_DATA_PUBLISH_INTERVAL * 2:
                publish_status()
                last_status_time = current_time

            # Update uptime
            machine.uptime_seconds = int(current_time - machine.last_maintenance)

            # Sleep for sensor update interval
            time.sleep(MACHINE_SENSOR_UPDATE_INTERVAL)

    except Exception as e:
        logger.error(f"Error in main loop: {e}")

    finally:
        # Cleanup
        logger.info("Shutting down...")
        machine.stop()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        logger.info("Folding machine service stopped")


if __name__ == "__main__":
    main()
