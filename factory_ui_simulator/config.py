import os
from util import resolve_address

# MQTT Configs
MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")  # Use env vars for flexibility
MQTT_RESOLVED_URL = resolve_address(MQTT_BROKER)
MQTT_PUBLIC_HOST = os.getenv("MQTT_PUBLIC_HOST", "localhost") # The host the browser should use
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_WS_PORT = int(os.getenv("MQTT_WS_PORT", 8083))

# Flask web app
WEBAPP_PORT = os.getenv("WEBAPP_PORT", 5001)  # If the port number is statically defined
API_BASE_URL = "http://localhost:" + str(WEBAPP_PORT) # use host IP address such as 10.0.1.2 not localhost

# Factory/site identifier - Used to target specific factory for commands and subscribe to its status
FACTORY_SITE_ID = os.getenv("FACTORY_SITE_ID", "tshirt-factory-001")

# UI integration: where the customer customizer / product designer is hosted
CUSTOMER_UI_URL = os.getenv("CUSTOMER_UI_URL", "http://localhost:8080")
CUSTOMER_UI_LABEL = os.getenv("CUSTOMER_UI_LABEL", "designer")

# REST polling interval for machine status (seconds)
MACHINE_DATA_REST_REQUEST_INTERVAL = int(os.getenv("MACHINE_DATA_REST_REQUEST_INTERVAL", 10))  # Default 10 s

# MQTT Topic Structure (NEW: factory-centric)
# All commands are sent to: factory/{FACTORY_SITE_ID}/{command_topic}
# All status is received from: factory/{FACTORY_SITE_ID}/{status_topic}
MQTT_TOPIC_MACHINES_STATUS = f"factory/{FACTORY_SITE_ID}/machines/status"
MQTT_TOPIC_PRODUCTION_STATUS = f"factory/{FACTORY_SITE_ID}/production/+/status"
MQTT_TOPIC_PRODUCTION_RESULT = f"factory/{FACTORY_SITE_ID}/production/+/result"
MQTT_TOPIC_PRODUCTION_REQUEST = f"factory/{FACTORY_SITE_ID}/production/request"
MQTT_TOPIC_TEST_REQUEST = f"factory/{FACTORY_SITE_ID}/test/request"
MQTT_TOPIC_SENSOR_UPDATE = f"factory/{FACTORY_SITE_ID}/sensor/update"
MQTT_TOPIC_CONFIG = f"factory/{FACTORY_SITE_ID}/config"

# Backward compatibility (legacy)
MQTT_TOPIC_MACHINE = "machine/data"
MQTT_TOPIC_PRODUCTION = f"factory/{FACTORY_SITE_ID}/production/#"
