"""
Customer Order UI Managers

Simplified managers for customer order interface that communicates with the factory
via MQTT for production requests and machine monitoring.
"""

import os
import json
import logging
import paho.mqtt.client as mqtt
import threading

# Configuration from environment variables
FACTORY_SITE_ID = os.getenv("FACTORY_SITE_ID", "tshirt-factory-001")
MQTT_BROKER = os.getenv("MQTT_BROKER", "tshirt-factory-001-mqtt")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_WS_PORT = int(os.getenv("MQTT_WS_PORT", 9001))
API_BASE_URL = os.getenv("API_URL", "http://localhost:5001")
MQTT_TOPIC_PRODUCTION = f"factory/{FACTORY_SITE_ID}/production/status"
MACHINE_DATA_REST_REQUEST_INTERVAL = int(os.getenv("MACHINE_DATA_REST_REQUEST_INTERVAL", 10))
WEBAPP_PORT = int(os.getenv("WEBAPP_PORT", 5002))

logger = logging.getLogger(__name__)

class SimpleMQTTPublisher:
    """Simple MQTT publisher for production requests"""
    def __init__(self, client_id):
        self.client_id = client_id
        self.client = mqtt.Client(client_id)
        self.is_connected = False
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect

    def on_connect(self, client, userdata, flags, rc):
        self.is_connected = True
        logger.info(f"MQTT connected: {self.client_id}")

    def on_disconnect(self, client, userdata, rc):
        self.is_connected = False
        logger.info(f"MQTT disconnected: {self.client_id}")

    def connect(self, broker, port):
        try:
            self.client.connect(broker, port, 60)
            self.client.loop_start()
            logger.info(f"Connected to MQTT broker {broker}:{port}")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT: {e}")

    def publish(self, topic, message):
        if self.is_connected:
            self.client.publish(topic, message)
            logger.info(f"Published to {topic}: {message}")
        else:
            logger.warning(f"MQTT not connected, cannot publish to {topic}")

# MQTT Publisher for production requests
production_mqtt_publisher = SimpleMQTTPublisher(f"customer-order-ui-{FACTORY_SITE_ID}")
production_mqtt_publisher.connect(MQTT_BROKER, MQTT_PORT)

# Mock machines list (will be populated from factory state)
machines = []

class MockMachine:
    """Mock machine for customer UI - simplified version"""
    def __init__(self, machine_id, name):
        self.id = machine_id
        self.name = name
        self.status = "idle"
        self.sensor_data = {}

    def to_json(self):
        return json.dumps({
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "sensor_data": self.sensor_data
        })

class MockMachineManager:
    """Mock machine manager for customer UI"""
    def __init__(self):
        self.machines = machines

    def update_machine(self, machine_id, data):
        # Mock implementation - doesn't actually update factory
        machine = next((m for m in self.machines if m.id == machine_id), None)
        if machine:
            if "failure_rate" in data:
                machine.failure_rate = data["failure_rate"]
            return machine
        return None

    def update_machine_sensor(self, machine_id, sensor_name, value):
        # Mock implementation - doesn't actually update factory
        machine = next((m for m in self.machines if m.id == machine_id), None)
        if machine:
            machine.sensor_data[sensor_name] = value
            return machine
        return None

    def run(self):
        # Mock run method
        pass

    def publish_machine_data(self):
        # Mock publish method
        pass

class MockProductionManager:
    """Mock production manager for customer UI"""
    def __init__(self):
        self.production_process = MockProductionProcess()

    def run(self):
        # Mock run method
        pass

class MockProductionProcess:
    """Mock production process"""
    def set_failure_rate(self, rate):
        # Mock method
        pass

# Initialize mock managers
machine_manager = MockMachineManager()
production_manager = MockProductionManager()

def create_response(data, status=200):
    """Create a JSON response"""
    from flask import jsonify
    return jsonify(data), status

def generate_random_product_details():
    """Generate random product details for testing"""
    import random
    colors = ["red", "blue", "green", "black", "white", "yellow"]
    sizes = ["S", "M", "L", "XL", "XXL"]
    return {
        "color": random.choice(colors),
        "size": random.choice(sizes),
        "quantity": random.randint(1, 100)
    }

def generate_random_test_case(machines_data):
    """Generate a random test case"""
    # Simplified test case generation
    return {
        "name": "random_test",
        "steps": [
            {
                "action": "production_request",
                "product_name": "T-Shirt",
                "details": generate_random_product_details()
            }
        ]
    }

# Initialize some mock machines
machines.extend([
    MockMachine("cutting-001", "cutting"),
    MockMachine("sewing-001", "sewing"),
    MockMachine("printing-001", "printing"),
    MockMachine("ironing-001", "ironing"),
    MockMachine("packaging-001", "packaging")
])