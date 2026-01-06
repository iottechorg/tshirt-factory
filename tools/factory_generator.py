#!/usr/bin/env python3
"""
Factory Generator from JSON Configuration

This tool generates a complete factory simulation from JSON configuration files.
It creates:
- Machine instances based on templates
- Workflow definitions
- Docker compose configuration
- Database schemas
- MQTT topics
"""

import json
import os
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Any
import argparse
try:
    import yaml
except Exception:
    yaml = None
    # fallback shim using json for environments without PyYAML
    import types
    def _yaml_dump(obj, stream=None, **kwargs):
        text = json.dumps(obj, indent=2)
        if stream:
            try:
                stream.write(text)
                return None
            except Exception:
                pass
        return text
    def _yaml_safe_load(s):
        return json.loads(s)
    yaml = types.SimpleNamespace(dump=_yaml_dump, safe_load=_yaml_safe_load)



class FactoryGenerator:
    """Generate factory components from JSON configuration"""

    def __init__(self, config_file: str, output_dir: str = "."):
        self.config_file = config_file
        self.output_dir = Path(output_dir)
        self.config = self.load_config()
        self.machine_templates = {}

    def load_config(self) -> Dict:
        """Load factory configuration from JSON"""
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def load_machine_template(self, template_file: str) -> Dict:
        """Load machine template from JSON"""
        if template_file in self.machine_templates:
            return self.machine_templates[template_file]

        # Try to find template file
        template_path = Path(template_file)
        if not template_path.exists():
            # Try relative to config file
            config_dir = Path(self.config_file).parent.parent
            template_path = config_dir / template_file

        if not template_path.exists():
            raise FileNotFoundError(f"Machine template not found: {template_file}")

        with open(template_path, 'r') as f:
            template = json.load(f)
            self.machine_templates[template_file] = template
            return template

    def generate_machine_class(self, machine_config: Dict, template: Dict) -> str:
        """Generate Python machine class from template"""
        machine_type = machine_config['machine_type']
        class_name = ''.join(word.capitalize() for word in machine_type.split('_'))

        # Generate sensor initialization
        sensors_init = []
        for sensor in template['sensors']:
            name = sensor['name']
            if sensor['initial_value'] == 'random':
                range_def = sensor['range']
                if 'min' in range_def and 'max' in range_def:
                    sensors_init.append(
                        f'            "{name}": random.uniform({range_def["min"]}, {range_def["max"]})'
                    )
                elif 'values' in range_def:
                    sensors_init.append(
                        f'            "{name}": random.choice({range_def["values"]})'
                    )
            else:
                sensors_init.append(f'            "{name}": {sensor["initial_value"]}')

        # Generate sensor updates
        sensor_updates = []
        for sensor in template['sensors']:
            name = sensor['name']
            behavior = sensor['update_behavior']

            if behavior['type'] == 'random_walk':
                params = behavior.get('parameters', {})
                variation = params.get('variation', 0.5)
                bounds_check = params.get('bounds_check', True)

                update_code = f'        self.sensor_data["{name}"] += random.uniform(-{variation}, {variation})'
                sensor_updates.append(update_code)

                if bounds_check and 'range' in sensor:
                    range_def = sensor['range']
                    if 'min' in range_def and 'max' in range_def:
                        bounds_code = f'        self.sensor_data["{name}"] = max({range_def["min"]}, min({range_def["max"]}, self.sensor_data["{name}"]))'
                        sensor_updates.append(bounds_code)

            elif behavior['type'] == 'sine_wave':
                params = behavior['parameters']
                sensor_updates.append(
                    f'        # Sine wave for {name} - implement in update loop'
                )

            elif behavior['type'] == 'static':
                sensor_updates.append(f'        # {name} is static')

        # Generate operations list
        operations = [op['name'] for op in template['operations']]
        operations_str = json.dumps(operations)

        # Generate class code
        class_code = f'''"""
{class_name} Machine Implementation
Auto-generated from template: {machine_config['template_file']}
"""
import sys
import os
import random
import time
import math
from typing import Dict, Any

sys.path.insert(0, '/app/shared')

from base_machine import BaseMachine


class {class_name}Machine(BaseMachine):
    """
    {template.get('machine_name', class_name)} - {template.get('description', '')}

    Category: {template.get('category', 'general')}

    Sensors:
'''
        for sensor in template['sensors']:
            class_code += f"    - {sensor['name']}: {sensor['type']} ({sensor['unit']})\n"

        class_code += f'''
    Operations:
'''
        for op in template['operations']:
            class_code += f"    - {op['name']}: {op.get('display_name', op['name'])}\n"

        class_code += f'''    """

    def __init__(self, machine_id: str, machine_name: str = "{machine_type}"):
        super().__init__(machine_id, "{machine_type}", machine_name)
        self.operations = {operations_str}

        # Template metadata
        self.template_info = {{
            "manufacturer": "{template.get('metadata', {}).get('manufacturer', 'Unknown')}",
            "model": "{template.get('metadata', {}).get('model', 'N/A')}",
            "category": "{template.get('category', 'general')}"
        }}

        # Telemetry configuration
        self.telemetry_interval = {template['telemetry_config']['publish_interval']}
        self.sensor_update_interval = {template['telemetry_config'].get('sensor_update_interval', 1.0)}

        # Initialize custom metrics
        self.custom_metrics = {{}}

    def _initialize_sensors(self) -> Dict[str, Any]:
        """Initialize sensor values from template"""
        return {{
  {',\n'.join(sensors_init)}
        }}

    def update_sensors(self):
        """Update sensor readings based on template behavior"""
        if not self.is_running:
            return

{chr(10).join(sensor_updates)}

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
        operations_templates = {json.dumps(template['operations'], indent=8)}
        for op in operations_templates:
            if op['name'] == operation_name:
                return op
        return {{}}

    def calculate_custom_metrics(self) -> Dict[str, float]:
        """Calculate custom metrics defined in template"""
        metrics = {{}}

        # Add template-defined metrics here
        # Example: "weld_quality_index": "(arc_voltage - 20) / 10 * 100"

        return metrics

    def process_operation(self, process_data: Dict) -> Dict:
        """Process an operation based on template configuration"""
        if not self.validate_process_data(process_data):
            return {{
                "status": "failed",
                "error": "Invalid process data",
                "machine_id": self.machine_id,
                "machine_type": self.machine_type
            }}

        operation = process_data.get("operation")
        op_template = self._get_operation_template(operation)

        # Calculate duration
        duration = self._calculate_duration(op_template, process_data)

        # Simulate processing
        time.sleep(min(duration, 2.0))  # Cap at 2 seconds for simulation

        # Check for failures
        if self._check_failures(op_template):
            return {{
                "status": "failed",
                "error": "Operation failed",
                "machine_id": self.machine_id,
                "machine_type": self.machine_type,
                "operation": operation
            }}

        # Apply sensor impacts
        self._apply_sensor_impacts(op_template)

        return {{
            "status": "success",
            "machine_id": self.machine_id,
            "machine_type": self.machine_type,
            "operation": operation,
            "outputs": op_template.get('outputs', []),
            "duration": duration,
            "timestamp": time.time()
        }}

    def _calculate_duration(self, op_template: Dict, process_data: Dict) -> float:
        """Calculate operation duration from template"""
        if not op_template:
            return 1.0

        duration_config = op_template.get('duration', {{}})
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
                conditions = failure_mode.get('conditions', {{}})
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
'''

        return class_code

    def generate_docker_compose(self) -> str:
        """Generate docker-compose configuration for factory in YAML format"""
        compose = {
            'volumes': {
                'mosquitto_data': None,
                'mosquitto_log': None,
                'postgres_data': None,
                'timescaledb_data': None,
                'redis_data': None
            },
            'networks': {
                f"{self.config['factory_id']}-network": {
                    'driver': 'bridge'
                }
            },
            'services': {}
        }

        # Add MQTT broker
        compose['services']['mqttbroker'] = {
            'image': 'eclipse-mosquitto:latest',
            'container_name': f"{self.config['factory_id']}-mqtt",
            'ports': ['31883:1883', '9001:9001'],
            'volumes': [
                './mqtt/mosquitto.conf:/mosquitto/config/mosquitto.conf',
                'mosquitto_data:/mosquitto/data',
                'mosquitto_log:/mosquitto/log'
            ],
            'networks': [f"{self.config['factory_id']}-network"],
            'restart': 'unless-stopped'
        }

        # Add databases
        compose['services']['postgres'] = {
            'image': 'postgres:15-alpine',
            'container_name': f"{self.config['factory_id']}-postgres",
            'environment': {
                'POSTGRES_USER': 'factory_user',
                'POSTGRES_PASSWORD': 'factory_pass',
                'POSTGRES_DB': self.config['database_config']['connection']['database']
            },
            'ports': ['5432:5432'],
            'volumes': [
                'postgres_data:/var/lib/postgresql/data',
                './database/init-postgres.sql:/docker-entrypoint-initdb.d/init-postgres.sql'
            ],
            'networks': [f"{self.config['factory_id']}-network"],
            'restart': 'unless-stopped'
        }

        # Add TimescaleDB for time-series data
        compose['services']['timescaledb'] = {
            'image': 'timescale/timescaledb:latest-pg15',
            'container_name': f"{self.config['factory_id']}-timescaledb",
            'environment': {
                'POSTGRES_USER': 'factory_user',
                'POSTGRES_PASSWORD': 'factory_pass',
                'POSTGRES_DB': 'factory_timeseries'
            },
            'ports': ['5433:5432'],
            'volumes': ['timescaledb_data:/var/lib/postgresql/data'],
            'networks': [f"{self.config['factory_id']}-network"],
            'restart': 'unless-stopped',
            'healthcheck': {
                'test': ['CMD', 'pg_isready', '-U', 'factory_user'],
                'interval': '10s',
                'timeout': '5s',
                'retries': 5
            }
        }

        # Add machines - FIXED: build context is now "." instead of "./services"
        for machine in self.config['machines']:
            if not machine.get('enabled', True):
                continue

            machine_id = machine['machine_id']
            machine_type = machine['machine_type']

            compose['services'][machine_id] = {
                'build': {
                    'context': '.',  # CHANGED: from './services' to '.'
                    'dockerfile': f"services/machines/{machine_type}/Dockerfile"  # CHANGED: added "services/" prefix
                },
                'container_name': machine_id,
                'environment': {
                    'MACHINE_ID': machine_id,
                    'MACHINE_TYPE': machine_type,
                    'MQTT_BROKER': 'mqttbroker',
                    'MQTT_PORT': 1883,
                    'FACTORY_SITE_ID': self.config.get('mqtt_config', {}).get('site_id', 'site-01'),
                    'MACHINE_SENSOR_UPDATE_INTERVAL': 2,
                    'MACHINE_DATA_PUBLISH_INTERVAL': 5,
                    'SERVICE_NAME': machine_id
                },
                'depends_on': ['mqttbroker'],
                'networks': [f"{self.config['factory_id']}-network"],
                'restart': 'unless-stopped'
            }

        # Convert to YAML string
        return yaml.dump(compose, default_flow_style=False, sort_keys=False)
        
    def copy_shared_module(self, factory_dir: Path):
        """Copy shared module (base_machine, mqtt_client, etc.) to generated factory"""
        print("Copying shared module...")

        # Source: root/shared directory (correct path)
        src_shared = Path(__file__).parent.parent / "shared"
        
        # Alternative: if the script is run from project root
        if not src_shared.exists():
            src_shared = Path("shared")
        
        if not src_shared.exists():
            print(f"  ⚠️  Warning: shared module not found at {src_shared}")
            print(f"  Looking for: {src_shared.absolute()}")
            return

        # Destination: factory/services/shared
        dest_shared = factory_dir / "services" / "shared"
        dest_shared.parent.mkdir(parents=True, exist_ok=True)

        if dest_shared.exists():
            shutil.rmtree(dest_shared)

        shutil.copytree(src_shared, dest_shared)
        print(f"  ✓ Copied shared module from {src_shared} to {dest_shared}")
        
        # Verify the copy worked
        if (dest_shared / "mqtt_client.py").exists():
            print(f"  ✓ Verified: mqtt_client.py copied successfully")
        else:
            print(f"  ❌ Error: mqtt_client.py not found after copy")

    def copy_orchestrator(self, factory_dir: Path):
        """Copy production orchestrator service to generated factory"""
        print("Copying production orchestrator...")

        src_orch = Path(__file__).parent.parent / "production-orchestrator"

        if not src_orch.exists():
            print(f"  ⚠️  Warning: orchestrator not found at {src_orch}")
            return

        dest_orch = factory_dir / "services" / "orchestrator"
        dest_orch.parent.mkdir(parents=True, exist_ok=True)

        if dest_orch.exists():
            shutil.rmtree(dest_orch)

        shutil.copytree(src_orch, dest_orch)
        print(f"  ✓ Copied orchestrator to {dest_orch}")

    def copy_monitoring_service(self, factory_dir: Path):
        """Copy monitoring service to generated factory"""
        print("Copying monitoring service...")

        src_mon = Path(__file__).parent.parent / "monitoring-service"

        if not src_mon.exists():
            print(f"  ⚠️  Warning: monitoring-service not found at {src_mon}")
            return

        dest_mon = factory_dir / "services" / "monitoring"
        dest_mon.parent.mkdir(parents=True, exist_ok=True)

        if dest_mon.exists():
            shutil.rmtree(dest_mon)

        shutil.copytree(src_mon, dest_mon)
        print(f"  ✓ Copied monitoring service to {dest_mon}")

    def copy_cloud_connectors(self, factory_dir: Path):
        """Copy cloud connector services (optional) to generated factory"""
        print("Copying cloud connectors...")

        src_cloud = Path(__file__).parent.parent / "cloud-connectors"

        if not src_cloud.exists():
            print(f"  ⚠️  Warning: cloud-connectors not found at {src_cloud}")
            return

        dest_cloud = factory_dir / "services" / "cloud-connectors"
        dest_cloud.parent.mkdir(parents=True, exist_ok=True)

        if dest_cloud.exists():
            shutil.rmtree(dest_cloud)

        shutil.copytree(src_cloud, dest_cloud)
        print(f"  ✓ Copied cloud connectors to {dest_cloud}")

    def generate_machine_service_wrapper(self, machine_type: str, factory_dir: Path):
        """Generate machine_service.py wrapper for each machine"""
        machine_service_code = f'''#!/usr/bin/env python3
"""
Machine Service Wrapper for {machine_type}
Auto-generated service runner
"""
import sys
import os
import time
import logging
import threading

# Add paths to include shared module
sys.path.insert(0, '/app/shared')
sys.path.insert(0, '/app')

from shared.mqtt_client import MQTTClientWrapper
from {machine_type}_machine import {machine_type.title().replace('_', '')}Machine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MachineService:
    """Service wrapper for machine"""

    def __init__(self):
        self.machine_id = os.getenv('MACHINE_ID', '{machine_type}-01')
        self.machine_type = os.getenv('MACHINE_TYPE', '{machine_type}')
        self.factory_site_id = os.getenv('FACTORY_SITE_ID', 'site-01')

        # MQTT configuration
        self.mqtt_broker = os.getenv('MQTT_BROKER', 'localhost')
        self.mqtt_port = int(os.getenv('MQTT_PORT', 1883))

        # Initialize machine
        self.machine = {machine_type.title().replace('_', '')}Machine(
            machine_id=self.machine_id,
            machine_name=f"{{self.machine_type}}-{{self.machine_id}}"
        )

        # Initialize MQTT client
        self.mqtt_client = MQTTClientWrapper(
            client_id=f"{{self.factory_site_id}}-{{self.machine_id}}",
            broker=self.mqtt_broker,
            port=self.mqtt_port
        )

        # Topics
        self.telemetry_topic = f"factory/{{self.factory_site_id}}/machines/{{self.machine_id}}/telemetry"
        self.status_topic = f"factory/{{self.factory_site_id}}/machines/{{self.machine_id}}/status"
        self.command_topic = f"factory/{{self.factory_site_id}}/machines/{{self.machine_id}}/command"
        self.operation_topic = f"factory/{{self.factory_site_id}}/machines/{{self.machine_id}}/operation"

        self.running = False

    def on_command(self, topic, payload):
        """Handle incoming commands"""
        try:
            command = payload.get('command')
            logger.info(f"Received command: {{command}}")

            if command == 'start':
                self.machine.start()
            elif command == 'stop':
                self.machine.stop()
            elif command == 'set_failure_rate':
                rate = payload.get('rate', 0.01)
                self.machine.set_failure_rate(rate)

        except Exception as e:
            logger.error(f"Error handling command: {{e}}")

    def on_operation(self, topic, payload):
        """Handle operation requests"""
        try:
            logger.info(f"Processing operation: {{payload}}")
            result = self.machine.process_operation(payload)

            # Publish operation result
            result_topic = f"factory/{{self.factory_site_id}}/machines/{{self.machine_id}}/operation/result"
            self.mqtt_client.publish(result_topic, result)

        except Exception as e:
            logger.error(f"Error processing operation: {{e}}")

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
                logger.error(f"Error publishing telemetry: {{e}}")
                time.sleep(5)

    def start(self):
        """Start the machine service"""
        logger.info(f"Starting machine service: {{self.machine_id}}")

        # Connect MQTT
        self.mqtt_client.connect()
        self.mqtt_client.loop_start()

        # Subscribe to topics
        self.mqtt_client.subscribe(self.command_topic, self.on_command)
        self.mqtt_client.subscribe(self.operation_topic, self.on_operation)

        # Start machine
        self.machine.start()
        self.running = True

        # Start telemetry thread
        telemetry_thread = threading.Thread(target=self.publish_telemetry, daemon=True)
        telemetry_thread.start()

        logger.info(f"Machine service started: {{self.machine_id}}")

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
'''

        service_file = factory_dir / "services" / "machines" / machine_type / "machine_service.py"
        service_file.parent.mkdir(parents=True, exist_ok=True)

        with open(service_file, 'w') as f:
            f.write(machine_service_code)

        # Make it executable
        os.chmod(service_file, 0o755)

    def generate_database_init_script(self) -> str:
        """Generate PostgreSQL initialization script for the factory"""
        db_name = self.config['database_config']['connection']['database']
        
        init_sql = f'''-- PostgreSQL Initialization Script for Factory Database

-- Create database user if not exists
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_user
      WHERE usename = 'factory_user'
   ) THEN
      CREATE USER factory_user WITH PASSWORD 'factory_pass';
   END IF;
END
$do$;

-- Create main database (if not connected via postgres service environment variable)
CREATE DATABASE IF NOT EXISTS {db_name};
GRANT ALL PRIVILEGES ON DATABASE {db_name} TO factory_user;

-- Connect to the database
\\c {db_name};

-- Machines table
CREATE TABLE IF NOT EXISTS machines (
    machine_id VARCHAR(100) PRIMARY KEY,
    machine_type VARCHAR(50) NOT NULL,
    machine_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Production orders table
CREATE TABLE IF NOT EXISTS production_orders (
    order_id VARCHAR(100) PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    product_details JSONB,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Production steps table
CREATE TABLE IF NOT EXISTS production_steps (
    step_id SERIAL PRIMARY KEY,
    order_id VARCHAR(100) REFERENCES production_orders(order_id),
    step_name VARCHAR(50) NOT NULL,
    machine_id VARCHAR(100) REFERENCES machines(machine_id),
    status VARCHAR(50) NOT NULL,
    process_data JSONB,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

-- Machine status log table
CREATE TABLE IF NOT EXISTS machine_status_log (
    log_id SERIAL PRIMARY KEY,
    machine_id VARCHAR(100) REFERENCES machines(machine_id),
    runtime_state VARCHAR(50) NOT NULL,
    total_operations INTEGER,
    failed_operations INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Machine telemetry table (for PostgreSQL storage when TimescaleDB unavailable)
CREATE TABLE IF NOT EXISTS machine_telemetry (
    telemetry_id SERIAL PRIMARY KEY,
    machine_id VARCHAR(100) NOT NULL,
    machine_type VARCHAR(50) NOT NULL,
    sensor_data JSONB NOT NULL,
    runtime_state VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_orders_status ON production_orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created ON production_orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_steps_order ON production_steps(order_id);
CREATE INDEX IF NOT EXISTS idx_status_log_machine ON machine_status_log(machine_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_machine ON machine_telemetry(machine_id, timestamp DESC);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO factory_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO factory_user;

-- Insert sample machines
INSERT INTO machines (machine_id, machine_type, machine_name) VALUES
    ('cutting-01', 'cutting', 'Cutting Machine 01'),
    ('sewing-01', 'sewing', 'Sewing Machine 01'),
    ('ironing-01', 'ironing', 'Ironing Machine 01'),
    ('printing-01', 'printing', 'Printing Machine 01')
ON CONFLICT (machine_id) DO NOTHING;
'''
        return init_sql

    def generate_mqtt_config(self, factory_dir: Path):
        """Generate mosquitto.conf for MQTT broker"""
        mqtt_config = '''# Mosquitto Configuration
listener 1883
protocol mqtt

listener 9001
protocol websockets

allow_anonymous true

# Persistence
persistence true
persistence_location /mosquitto/data/

# Logging
log_dest file /mosquitto/log/mosquitto.log
log_dest stdout
log_type all
'''

        mqtt_dir = factory_dir / "mqtt"
        mqtt_dir.mkdir(exist_ok=True)

        config_file = mqtt_dir / "mosquitto.conf"
        with open(config_file, 'w') as f:
            f.write(mqtt_config)

        print(f"  ✓ Generated MQTT config")

    def update_docker_compose_with_services(self, compose: Dict) -> Dict:
        """Add orchestrator and monitoring services to docker-compose"""
        factory_id = self.config['factory_id']
        network = f"{factory_id}-network"

        # Add orchestrator - FIXED build context
        compose['services']['orchestrator'] = {
            'build': {
                'context': '.',  # CHANGED: from './services' to '.'
                'dockerfile': 'services/orchestrator/Dockerfile'  # CHANGED: added "services/" prefix
            },
            'container_name': f"{factory_id}-orchestrator",
            'environment': {
                'FACTORY_ID': factory_id,
                'MQTT_BROKER': 'mqttbroker',
                'MQTT_PORT': 1883,
                'POSTGRES_HOST': 'postgres',
                'POSTGRES_DB': self.config['database_config']['connection']['database'],
                'POSTGRES_USER': 'factory_user',
                'POSTGRES_PASSWORD': 'factory_pass'
            },
            'depends_on': ['mqttbroker', 'postgres'],
            'networks': [network],
            'restart': 'unless-stopped',
            'volumes': ['./workflows:/app/workflows:ro']
        }

        # Add monitoring service - FIXED build context
        compose['services']['monitoring'] = {
            'build': {
                'context': '.',  # CHANGED: from './services' to '.'
                'dockerfile': 'services/monitoring/Dockerfile'  # CHANGED: added "services/" prefix
            },
            'container_name': f"{factory_id}-monitoring",
            'environment': {
                'FACTORY_ID': factory_id,
                'MQTT_BROKER': 'mqttbroker',
                'MQTT_PORT': 1883,
                'FACTORY_SITE_ID': 'site-01',
                'DB_HOST': 'postgres',
                'DB_PORT': 5432,
                'DB_NAME': self.config['database_config']['connection']['database'],
                'DB_USER': 'factory_user',
                'DB_PASSWORD': 'factory_pass',
                'TIMESCALE_HOST': 'timescaledb',
                'TIMESCALE_PORT': 5432,
                'TIMESCALE_DB': 'factory_timeseries',
                'TIMESCALE_USER': 'factory_user',
                'TIMESCALE_PASSWORD': 'factory_pass'
            },
            'depends_on': ['mqttbroker', 'postgres', 'timescaledb'],
            'networks': [network],
            'restart': 'unless-stopped'
        }

        # Add config publisher service so the generated factory publishes its config at startup
        compose['services']['config-publisher'] = {
            'build': {
                'context': '.',
                'dockerfile': 'services/config_publisher/Dockerfile'
            },
            'container_name': f"{factory_id}-config-publisher",
            'environment': {
                'FACTORY_ID': factory_id,
                'MQTT_BROKER': 'mqttbroker',
                'MQTT_PORT': 1883
            },
            'depends_on': ['mqttbroker'],
            'networks': [network],
            'restart': 'unless-stopped',
            'volumes': [f"./factory-config.json:/app/factory-config.json:ro"]
        }

        return compose

    def generate_machine_dockerfile(self, machine_type: str, factory_dir: Path):
        """Generate Dockerfile for machine service with correct paths"""
        dockerfile_content = f'''FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY services/shared/requirements.txt /app/shared-requirements.txt
RUN pip install --no-cache-dir -r /app/shared-requirements.txt

# Copy shared module
COPY services/shared /app/shared

# Copy machine code
COPY services/machines/{machine_type} /app/machine

WORKDIR /app/machine

# Run machine service
CMD ["python3", "machine_service.py"]
'''

        dockerfile = factory_dir / "services" / "machines" / machine_type / "Dockerfile"
        dockerfile.parent.mkdir(parents=True, exist_ok=True)

        with open(dockerfile, 'w') as f:
            f.write(dockerfile_content)

    def generate_orchestrator_dockerfile(self, factory_dir: Path):
        """Generate Dockerfile for orchestrator service"""
        dockerfile_content = '''FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY services/shared/requirements.txt /app/shared-requirements.txt
RUN pip install --no-cache-dir -r /app/shared-requirements.txt

# Copy shared module
COPY services/shared /app/shared

# Copy orchestrator code
COPY services/orchestrator /app/orchestrator

WORKDIR /app/orchestrator

# Run orchestrator
CMD ["python3", "orchestrator.py"]
'''

        dockerfile = factory_dir / "services" / "orchestrator" / "Dockerfile"
        dockerfile.parent.mkdir(parents=True, exist_ok=True)

        with open(dockerfile, 'w') as f:
            f.write(dockerfile_content)

    def generate_monitoring_dockerfile(self, factory_dir: Path):
        """Generate Dockerfile for monitoring service"""
        dockerfile_content = '''FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY services/shared/requirements.txt /app/shared-requirements.txt
RUN pip install --no-cache-dir -r /app/shared-requirements.txt

# Copy shared module
COPY services/shared /app/shared

# Copy monitoring code
COPY services/monitoring /app/monitoring

WORKDIR /app/monitoring

# Run monitoring service
CMD ["python3", "monitoring_service.py"]
'''

        dockerfile = factory_dir / "services" / "monitoring" / "Dockerfile"
        dockerfile.parent.mkdir(parents=True, exist_ok=True)

        with open(dockerfile, 'w') as f:
            f.write(dockerfile_content)

    def generate_config_publisher_files(self, factory_dir: Path):
        """Generate a small service that publishes factory-config.json to MQTT at startup."""
        svc_dir = factory_dir / "services" / "config_publisher"
        svc_dir.mkdir(parents=True, exist_ok=True)

        publish_py = '''#!/usr/bin/env python3
import os
import json
import time
import logging
import sys
import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

FACTORY_ID = os.getenv("FACTORY_ID", "{factory_id}")
MQTT_BROKER = os.getenv("MQTT_BROKER", "mqttbroker")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
CONFIG_PATH = os.getenv("CONFIG_PATH", "/app/factory-config.json")

TOPIC_CONFIG = f"factory/{{FACTORY_ID}}/config"
TOPIC_REQUEST = f"factory/{{FACTORY_ID}}/config/request"

def load_config(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config from {path}: {e}")
        return None

def publish_config(client, config):
    payload = json.dumps(config)
    client.publish(TOPIC_CONFIG, payload, qos=1, retain=True)
    logger.info(f"Published factory config to topic {TOPIC_CONFIG}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT broker")
        client.subscribe(TOPIC_REQUEST)
        cfg = load_config(CONFIG_PATH)
        if cfg:
            publish_config(client, cfg)
    else:
        logger.error(f"MQTT connection failed with rc={rc}")

def on_message(client, userdata, msg):
    logger.info(f"Received config request on {msg.topic}")
    cfg = load_config(CONFIG_PATH)
    if cfg:
        publish_config(client, cfg)

def main():
    client = mqtt.Client(client_id=f"config-publisher-{FACTORY_ID}")
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    except Exception as e:
        logger.error(f"Unable to connect to MQTT broker {MQTT_BROKER}:{MQTT_PORT} - {e}")
        sys.exit(1)
    client.loop_start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down config publisher")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
'''.replace('{factory_id}', self.config.get('factory_id', 'factory-001'))

        with open(svc_dir / 'publish_config.py', 'w') as f:
            f.write(publish_py)
        os.chmod(svc_dir / 'publish_config.py', 0o755)

        with open(svc_dir / 'requirements.txt', 'w') as f:
            f.write('paho-mqtt>=1.6\n')

        dockerfile = svc_dir / 'Dockerfile'
        dockerfile_content = f'''FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY publish_config.py /app/publish_config.py
COPY ../../../factory-config.json /app/factory-config.json
CMD ["python", "/app/publish_config.py"]
'''
        with open(dockerfile, 'w') as f:
            f.write(dockerfile_content)


    def generate_factory(self):
        """Generate complete factory from configuration"""
        factory_id = self.config['factory_id']
        factory_name = self.config['factory_name']

        print(f"Generating factory: {factory_name} ({factory_id})")
        print(f"Factory type: {self.config['factory_type']}")
        print(f"Machines: {len(self.config['machines'])}")
        print(f"Workflows: {len(self.config['workflows'])}")
        print()

        # Create output directories
        factory_dir = self.output_dir / factory_id
        services_dir = factory_dir / "services"
        machines_dir = services_dir / "machines"
        workflows_dir = factory_dir / "workflows"
        mqtt_dir = factory_dir / "mqtt"

        # Clean and create directories
        if factory_dir.exists():
            shutil.rmtree(factory_dir)
        
        factory_dir.mkdir(parents=True, exist_ok=True)
        services_dir.mkdir(exist_ok=True)
        machines_dir.mkdir(exist_ok=True)
        workflows_dir.mkdir(exist_ok=True)
        mqtt_dir.mkdir(exist_ok=True)
        
        # Create database directory and initialization script
        db_dir = factory_dir / "database"
        db_dir.mkdir(exist_ok=True)
        
        # Generate database initialization script
        init_sql = self.generate_database_init_script()
        init_sql_file = db_dir / "init-postgres.sql"
        with open(init_sql_file, 'w') as f:
            f.write(init_sql)

        # Generate machine classes and Dockerfiles
        print("Generating machine classes and Dockerfiles...")
        unique_types = set()
        for machine in self.config['machines']:
            if not machine.get('enabled', True):
                continue
                
            machine_type = machine['machine_type']
            if machine_type in unique_types:
                continue
            unique_types.add(machine_type)

            print(f"  - {machine_type}")

            # Load template
            template = self.load_machine_template(machine['template_file'])

            # Generate machine class
            machine_code = self.generate_machine_class(machine, template)

            # Write machine class
            machine_file = machines_dir / machine_type / f"{machine_type}_machine.py"
            machine_file.parent.mkdir(parents=True, exist_ok=True)
            with open(machine_file, 'w') as f:
                f.write(machine_code)

            # Generate machine service wrapper
            self.generate_machine_service_wrapper(machine_type, factory_dir)

            # Generate Dockerfile for machine
            self.generate_machine_dockerfile(machine_type, factory_dir)

        # Generate workflows
        print("\nGenerating workflows...")
        for workflow in self.config['workflows']:
            workflow_id = workflow['workflow_id']
            print(f"  - {workflow_id}")

            workflow_file = workflows_dir / f"{workflow_id}.json"
            with open(workflow_file, 'w') as f:
                json.dump(workflow, f, indent=2)

        # Copy shared services
        print("\nCopying shared services...")
        self.copy_shared_module(factory_dir)
        self.copy_orchestrator(factory_dir)
        self.copy_monitoring_service(factory_dir)
        self.copy_cloud_connectors(factory_dir)

        # Generate service Dockerfiles
        print("\nGenerating service Dockerfiles...")
        self.generate_orchestrator_dockerfile(factory_dir)
        self.generate_monitoring_dockerfile(factory_dir)

        # Generate MQTT configuration
        print("\nGenerating MQTT configuration...")
        self.generate_mqtt_config(factory_dir)

        # Generate docker-compose with proper build context
        print("\nGenerating docker-compose configuration...")
        
        # Generate base compose configuration
        compose_yaml = self.generate_docker_compose()
        compose_dict = yaml.safe_load(compose_yaml)
        
        # Add orchestrator and monitoring services
        compose_dict = self.update_docker_compose_with_services(compose_dict)
        
        # Write as proper YAML
        compose_file = factory_dir / "docker-compose.yml"
        with open(compose_file, 'w') as f:
            yaml.dump(compose_dict, f, default_flow_style=False, sort_keys=False)
        
        print(f"  ✓ Generated docker-compose.yml")

        # Generate factory configuration file
        print("\nGenerating factory configuration...")
        config_copy_file = factory_dir / "factory-config.json"
        with open(config_copy_file, 'w') as f:
            json.dump(self.config, f, indent=2)

        # Generate config-publisher service files so factories auto-publish their config
        print("\nGenerating config-publisher service files...")
        self.generate_config_publisher_files(factory_dir)

        # Generate requirements.txt for shared modules
        print("\nGenerating requirements file...")
        requirements_content = '''paho-mqtt>=2.0.0
psycopg2-binary>=2.9.0
pyyaml>=6.0
pydantic>=2.0.0
redis>=4.5.0
requests>=2.28.0
'''
        requirements_file = factory_dir / "services" / "shared" / "requirements.txt"
        with open(requirements_file, 'w') as f:
            f.write(requirements_content)

        # Generate README
        print("\nGenerating documentation...")
        readme = self._generate_readme()
        readme_file = factory_dir / "README.md"
        with open(readme_file, 'w') as f:
            f.write(readme)

        # Generate startup script
        print("\nGenerating startup scripts...")
        self._generate_startup_scripts(factory_dir)

        print(f"\n✅ Factory generated successfully in: {factory_dir}")
        print(f"\nNext steps:")
        print(f"1. cd {factory_dir}")
        print(f"2. docker compose up --build")
        print(f"3. Start production workflows")

        # Print factory summary
        self._print_factory_summary()

    def _generate_startup_scripts(self, factory_dir: Path):
        """Generate startup scripts for the factory"""
        
        # Generate start.sh
        start_script = '''#!/bin/bash
echo "🏭 Starting Factory: $(basename $(pwd))"
echo "======================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build and start services
echo "Building and starting factory services..."
docker compose up --build -d

echo ""
echo "✅ Factory started successfully!"
echo ""
echo "📊 Monitoring:"
echo "   MQTT Messages: mosquitto_sub -h localhost -p 31883 -t 'factory/#' -v"
echo "   Logs: docker compose logs -f"
echo ""
echo "🛑 To stop: docker compose down"
'''

        start_file = factory_dir / "start-factory.sh"
        with open(start_file, 'w') as f:
            f.write(start_script)
        start_file.chmod(0o755)

        # Generate stop.sh
        stop_script = '''#!/bin/bash
echo "🛑 Stopping Factory: $(basename $(pwd))"
docker compose down
echo "✅ Factory stopped"
'''

        stop_file = factory_dir / "stop-factory.sh"
        with open(stop_file, 'w') as f:
            f.write(stop_script)
        stop_file.chmod(0o755)

    def _print_factory_summary(self):
        """Print a summary of the generated factory"""
        factory_id = self.config['factory_id']
        
        print(f"\n🏭 Factory Summary: {self.config['factory_name']}")
        print("=" * 50)
        
        # Machines summary
        print(f"\n📦 Machines ({len(self.config['machines'])}):")
        for machine in self.config['machines']:
            if machine.get('enabled', True):
                status = "✅" 
            else:
                status = "❌"
            print(f"   {status} {machine['machine_id']} ({machine['machine_type']})")
        
        # Workflows summary
        print(f"\n📋 Workflows ({len(self.config['workflows'])}):")
        for workflow in self.config['workflows']:
            print(f"   📄 {workflow['workflow_id']}: {workflow['workflow_name']}")
        
        # Services summary
        print(f"\n🔧 Services:")
        print("   ✅ MQTT Broker (mosquitto)")
        print("   ✅ PostgreSQL Database")
        print("   ✅ Production Orchestrator")
        print("   ✅ Monitoring Service")
        
        # Access information
        print(f"\n🌐 Access Information:")
        print(f"   MQTT Broker:    localhost:31883")
        print(f"   Database:       localhost:5432")
        print(f"   MQTT WebSocket: localhost:9001")
        
        # Quick commands
        print(f"\n⚡ Quick Commands:")
        print(f"   Monitor MQTT:    mosquitto_sub -h localhost -p 31883 -t 'factory/#' -v")
        print(f"   View Logs:       docker compose logs -f")
        print(f"   Stop Factory:    docker compose down")
        print(f"   Restart:         docker compose restart")
        
        # Production example
        if self.config['workflows']:
            workflow = self.config['workflows'][0]
            print(f"\n🎯 Start Production:")
            print(f"   mosquitto_pub -h localhost -p 31883 \\")
            print(f"     -t 'factory/{self.config.get('mqtt_config', {}).get('site_id', 'site-01')}/production/request' \\")
            print(f"     -m '{{\"product_type\": \"{workflow['product_type']}\", \"quantity\": 1}}'")


    def _generate_readme(self) -> str:
        """Generate README for factory"""
        factory_name = self.config['factory_name']
        factory_type = self.config['factory_type']

        readme = f'''# {factory_name}

{self.config.get('description', '')}

## Factory Configuration

- **Type**: {factory_type}
- **ID**: {self.config['factory_id']}
- **Machines**: {len(self.config['machines'])}
- **Workflows**: {len(self.config['workflows'])}

## Machines

'''
        for machine in self.config['machines']:
            readme += f"- **{machine['machine_id']}**: {machine.get('instance_name', machine['machine_type'])}\n"

        readme += '''
## Workflows

'''
        for workflow in self.config['workflows']:
            readme += f"- **{workflow['workflow_id']}**: {workflow['workflow_name']} ({len(workflow['steps'])} steps)\n"

        readme += f'''

## Quick Start

```bash
# Start factory
docker compose up --build

# Monitor MQTT
mosquitto_sub -h localhost -p 31883 -t "factory/#" -v

# Send production order
mosquitto_pub -h localhost -p 31883 \\
  -t "factory/{self.config.get('mqtt_config', {}).get('site_id', 'site-01')}/production/request" \\
  -m '{{"product_type": "{self.config['workflows'][0]['product_type']}", "quantity": 1}}'
```

## Production Configuration

- **Mode**: {self.config['production_config']['mode']}
- **Target Rate**: {self.config['production_config']['target_rate']['value']} {self.config['production_config']['target_rate']['unit']}
- **Quality Control**: {'Enabled' if self.config['production_config'].get('quality_control', {}).get('enabled') else 'Disabled'}

## Generated Files

This factory was auto-generated from: `{self.config_file}`

Generated: {self.config.get('metadata', {}).get('created_date', 'N/A')}
Version: {self.config.get('metadata', {}).get('version', '1.0.0')}
'''

        return readme


def main():
    parser = argparse.ArgumentParser(
        description='Generate factory simulation from JSON configuration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Generate automotive factory
  python factory_generator.py factory-configs/automotive-assembly-plant.json

  # Generate food processing plant
  python factory_generator.py factory-configs/food-processing-plant.json \\
    --output generated-factories

  # Generate custom factory
  python factory_generator.py my-factory-config.json
        '''
    )

    parser.add_argument('config_file', help='Factory configuration JSON file')
    parser.add_argument('--output', '-o', default='generated-factories',
                        help='Output directory for generated factory (default: generated-factories)')

    args = parser.parse_args()

    if not os.path.exists(args.config_file):
        print(f"Error: Configuration file not found: {args.config_file}")
        sys.exit(1)

    try:
        generator = FactoryGenerator(args.config_file, args.output)
        generator.generate_factory()
    except Exception as e:
        print(f"Error generating factory: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
