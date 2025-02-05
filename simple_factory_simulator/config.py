import os
from util import resolve_address
# MQTT Configs
MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")  # Use env vars for flexibility
MQTT_RESOLVED_URL = resolve_address(MQTT_BROKER)
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC_MACHINE = "machine/data"
MQTT_TOPIC_PRODUCTION = "production/data"
MQTT_WS_PORT = int(os.getenv("MQTT_WS_PORT", 8083))

# Flask web app
WEBAPP_PORT = os.getenv("WEBAPP_PORT", 5001)  # If the port number is statically defined
API_BASE_URL = "http://localhost:" + str(WEBAPP_PORT) # use host IP address such as 10.0.1.2 not localhost

# Simulation app
PRODUCTION_SUCCESS_RATE = float(os.getenv("PRODUCTION_SUCCESS_RATE", 0.99))  # Default 90% success
MACHINE_NAMES = ["cutting", "sewing", "ironing", "printing"]

PRODUCTION_LOOP_INTERVAL = int(os.getenv("PRODUCTION_LOOP_INTERVAL", 10))  # Default 10 s
MACHINE_DATA_PUBLISH_INTERVAL = int(os.getenv("MACHINE_DATA_PUBLISH_INTERVAL", 5))  # Default 10 s
MACHINE_DATA_REST_REQUEST_INTERVAL = int(os.getenv("MACHINE_DATA_REST_REQUEST_INTERVAL", 10))  # Default 10 s
