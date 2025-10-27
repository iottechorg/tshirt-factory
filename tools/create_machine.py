#!/usr/bin/env python3
"""
Machine Generator Tool
Creates a new machine service with all necessary files following the standard structure.

Usage:
    python create_machine.py <machine_name> --sensors sensor1:type sensor2:type ...

Example:
    python create_machine.py drying --sensors temperature:float humidity:float fan_speed:float
"""

import os
import sys
import argparse
import json
from pathlib import Path

# Template for machine class
MACHINE_CLASS_TEMPLATE = '''"""
{machine_name_title} Machine Implementation
"""
import random
from typing import Dict, Any
from base_machine import BaseMachine


class {machine_class}Machine(BaseMachine):
    """
    {machine_name_title} machine for production line.

    Sensors:
{sensor_docs}
    """

    def __init__(self, machine_id: str, machine_name: str = "{machine_name}"):
        super().__init__(machine_id, "{machine_name}", machine_name)
        self.operations = {operations_list}

    def _initialize_sensors(self) -> Dict[str, Any]:
        """Initialize sensor values"""
        return {{
{sensor_init}
        }}

    def update_sensors(self):
        """Update sensor readings with realistic variations"""
        if not self.is_running:
            return

{sensor_updates}

    def validate_process_data(self, process_data: Dict) -> bool:
        """
        Validate that process data contains required fields.

        Override this method to add specific validation for your machine.
        """
        # Basic validation - check for process_data dict
        if not isinstance(process_data, dict):
            return False

        # Add your required fields here
        # required_fields = ["input_material", "operation_type"]
        # return all(field in process_data for field in required_fields)

        return True

    def process_operation(self, process_data: Dict) -> Dict:
        """
        Process an operation on this machine.

        Args:
            process_data: Dictionary containing operation parameters

        Returns:
            Result dictionary with status and outputs
        """
        if not self.validate_process_data(process_data):
            return {{
                "status": "failed",
                "error": "Invalid process data",
                "machine_id": self.machine_id,
                "machine_type": self.machine_type
            }}

        operation = process_data.get("operation", "default_operation")

        if operation not in self.operations:
            return {{
                "status": "failed",
                "error": f"Unknown operation: {{operation}}",
                "machine_id": self.machine_id,
                "machine_type": self.machine_type
            }}

        # Simulate processing time and potential failure
        import time
        time.sleep(random.uniform(0.5, 2.0))

        if self.simulate_failure():
            return {{
                "status": "failed",
                "error": "Machine failure during operation",
                "machine_id": self.machine_id,
                "machine_type": self.machine_type,
                "operation": operation
            }}

        return {{
            "status": "success",
            "machine_id": self.machine_id,
            "machine_type": self.machine_type,
            "operation": operation,
            "output": f"processed_{{operation}}",
            "timestamp": time.time()
        }}
'''

# Template for machine service
MACHINE_SERVICE_TEMPLATE = '''"""
{machine_name_title} Machine Service - Main Entry Point
"""
import sys
import os
import time
import logging
import signal
import json

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../shared'))

from {machine_name}_machine import {machine_class}Machine
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

        logger.info(f"Received command: {{command_type}}")

        if command_type == "update_sensor":
            sensor_name = command.get("sensor_name")
            value = command.get("value")
            if sensor_name and value is not None:
                machine.update_sensor_value(sensor_name, value)
                logger.info(f"Updated sensor {{sensor_name}} to {{value}}")

        elif command_type == "set_failure_rate":
            rate = command.get("rate")
            if rate is not None:
                machine.set_failure_rate(float(rate))
                logger.info(f"Updated failure rate to {{rate}}")

        elif command_type == "process":
            process_data = command.get("process_data")
            if process_data:
                result = machine.process_operation(process_data)
                logger.info(f"Process result: {{result['status']}}")
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
        logger.error(f"Invalid JSON in command: {{e}}")
    except Exception as e:
        logger.error(f"Error handling command: {{e}}")


def publish_status():
    """Publish machine status"""
    status_topic = get_machine_status_topic("{machine_name}", machine.machine_id)
    status = machine.get_status()
    mqtt_client.publish_json(status_topic, status)


def publish_telemetry():
    """Publish machine telemetry"""
    telemetry_topic = get_machine_telemetry_topic("{machine_name}", machine.machine_id)
    telemetry = machine.get_telemetry()
    mqtt_client.publish_json(telemetry_topic, telemetry)


def main():
    """Main service loop"""
    global machine, mqtt_client, running

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Get machine ID from environment or generate one
    machine_id = MACHINE_ID or f"{machine_name}-{{int(time.time())}}"
    logger.info(f"Starting {machine_name_title} Machine Service: {{machine_id}}")

    # Initialize machine
    machine = {machine_class}Machine(machine_id)
    machine.start()

    # Initialize MQTT client
    mqtt_client = MQTTClient(
        client_id=f"{machine_name}-machine-{{machine_id}}",
        broker=MQTT_BROKER,
        port=MQTT_PORT,
        keepalive=MQTT_KEEPALIVE
    )

    # Connect to MQTT broker
    if not mqtt_client.connect():
        logger.error("Failed to connect to MQTT broker, exiting...")
        return

    # Subscribe to command topic
    command_topic = get_machine_command_topic("{machine_name}", machine_id)
    mqtt_client.subscribe(command_topic, handle_command)

    # Start MQTT loop
    mqtt_client.loop_start()

    logger.info(f"{machine_name_title} machine {{machine_id}} is running...")
    logger.info(f"Listening for commands on: {{command_topic}}")

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
        logger.error(f"Error in main loop: {{e}}")

    finally:
        # Cleanup
        logger.info("Shutting down...")
        machine.stop()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        logger.info("{machine_name_title} machine service stopped")


if __name__ == "__main__":
    main()
'''

DOCKERFILE_TEMPLATE = '''FROM python:3.9-slim

WORKDIR /app

# Copy shared modules
COPY services/shared /app/shared

# Copy machine-specific files
COPY services/machines/{machine_name} /app/{machine_name}

# Install dependencies
RUN pip install --no-cache-dir paho-mqtt

# Set Python path
ENV PYTHONPATH=/app

WORKDIR /app/{machine_name}

CMD ["python", "machine_service.py"]
'''

DOCKERIGNORE_TEMPLATE = '''__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info
dist
build
.git
.gitignore
README.md
.env
venv
'''


def create_machine(machine_name: str, sensors: dict, base_path: str):
    """
    Create a new machine with all necessary files.

    Args:
        machine_name: Name of the machine (e.g., 'drying', 'cutting')
        sensors: Dictionary of sensor_name: sensor_type
        base_path: Base path of the project
    """
    # Validate machine name
    if not machine_name.isalnum():
        raise ValueError(f"Machine name must be alphanumeric (no hyphens or underscores): {machine_name}")

    machine_class = machine_name.capitalize()
    machine_name_title = machine_name.capitalize()

    # Create machine directory
    machine_dir = Path(base_path) / "services" / "machines" / machine_name
    machine_dir.mkdir(parents=True, exist_ok=True)

    print(f"Creating machine: {machine_name}")
    print(f"Machine directory: {machine_dir}")

    # Generate sensor documentation
    sensor_docs = "\n".join([f"    - {name}: {stype}" for name, stype in sensors.items()])

    # Generate sensor initialization
    sensor_ranges = {
        "temperature": (20.0, 80.0),
        "humidity": (30.0, 90.0),
        "pressure": (0.5, 2.0),
        "speed": (0.0, 100.0),
        "level": (0.0, 100.0),
        "voltage": (110.0, 240.0),
        "current": (0.0, 10.0),
        "position": (0.0, 100.0),
    }

    sensor_init_lines = []
    for name, stype in sensors.items():
        # Try to guess appropriate range based on sensor name
        range_val = (0.0, 100.0)  # default
        for key, val in sensor_ranges.items():
            if key in name.lower():
                range_val = val
                break

        sensor_init_lines.append(f'            "{name}": random.uniform({range_val[0]}, {range_val[1]})')

    sensor_init = ",\n".join(sensor_init_lines)

    # Generate sensor updates
    sensor_update_lines = []
    for name in sensors.keys():
        sensor_update_lines.append(f'        self.sensor_data["{name}"] += random.uniform(-0.5, 0.5)')

    sensor_updates = "\n".join(sensor_update_lines)

    # Generate operations list (default operations)
    operations_list = f'["process_{machine_name}", "inspect", "calibrate"]'

    # Create machine class file
    machine_class_content = MACHINE_CLASS_TEMPLATE.format(
        machine_name=machine_name,
        machine_name_title=machine_name_title,
        machine_class=machine_class,
        sensor_docs=sensor_docs,
        sensor_init=sensor_init,
        sensor_updates=sensor_updates,
        operations_list=operations_list
    )

    machine_file = machine_dir / f"{machine_name}_machine.py"
    with open(machine_file, 'w') as f:
        f.write(machine_class_content)
    print(f"Created: {machine_file}")

    # Create machine service file
    service_content = MACHINE_SERVICE_TEMPLATE.format(
        machine_name=machine_name,
        machine_name_title=machine_name_title,
        machine_class=machine_class
    )

    service_file = machine_dir / "machine_service.py"
    with open(service_file, 'w') as f:
        f.write(service_content)
    print(f"Created: {service_file}")

    # Create Dockerfile
    dockerfile_content = DOCKERFILE_TEMPLATE.format(machine_name=machine_name)
    dockerfile = machine_dir / "Dockerfile"
    with open(dockerfile, 'w') as f:
        f.write(dockerfile_content)
    print(f"Created: {dockerfile}")

    # Create .dockerignore
    dockerignore = machine_dir / ".dockerignore"
    with open(dockerignore, 'w') as f:
        f.write(DOCKERIGNORE_TEMPLATE)
    print(f"Created: {dockerignore}")

    # Create __init__.py
    init_file = machine_dir / "__init__.py"
    with open(init_file, 'w') as f:
        f.write(f'"""Package for {machine_name_title} Machine"""\n')
    print(f"Created: {init_file}")

    print(f"\n✅ Machine '{machine_name}' created successfully!")
    print(f"\nNext steps:")
    print(f"1. Review and customize the machine class: {machine_file}")
    print(f"2. Add the machine to docker-compose.microservices.yml")
    print(f"3. Register the machine in the orchestrator")
    print(f"4. Create workflows that use this machine")


def main():
    parser = argparse.ArgumentParser(
        description='Create a new machine service with standard structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Create a drying machine with temperature and humidity sensors
  python create_machine.py drying --sensors temperature:float humidity:float fan_speed:float

  # Create a labeling machine
  python create_machine.py labeling --sensors label_position:float dispenser_level:float print_quality:float
        '''
    )

    parser.add_argument('machine_name', help='Name of the machine (alphanumeric, no hyphens)')
    parser.add_argument('--sensors', nargs='+', required=True,
                        help='Sensor definitions in format name:type (e.g., temperature:float)')
    parser.add_argument('--base-path', default='.',
                        help='Base path of the project (default: current directory)')

    args = parser.parse_args()

    # Parse sensors
    sensors = {}
    for sensor_def in args.sensors:
        if ':' not in sensor_def:
            print(f"Error: Invalid sensor definition '{sensor_def}'. Use format name:type")
            sys.exit(1)

        name, stype = sensor_def.split(':', 1)
        sensors[name] = stype

    try:
        create_machine(args.machine_name, sensors, args.base_path)
    except Exception as e:
        print(f"Error creating machine: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
