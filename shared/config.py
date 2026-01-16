"""
Shared configuration for all factory services
"""
import os

# MQTT Broker Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "mqttbroker")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_WS_PORT = int(os.getenv("MQTT_WS_PORT", 9001))
MQTT_KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", 60))

# Factory Configuration
FACTORY_SITE_ID = os.getenv("FACTORY_SITE_ID", os.getenv("FACTORY_ID", "site-01"))
print(f"DEBUG: FACTORY_SITE_ID={FACTORY_SITE_ID}, FACTORY_ID={os.getenv('FACTORY_ID')}, FACTORY_SITE_ID_ENV={os.getenv('FACTORY_SITE_ID')}")

# MQTT Topic Structure (ISA-95 compliant)
def get_machine_status_topic(machine_type, machine_id):
    """Get MQTT topic for machine status updates"""
    return f"factory/{FACTORY_SITE_ID}/machine/{machine_type}/{machine_id}/status"

def get_machine_telemetry_topic(machine_type, machine_id):
    """Get MQTT topic for machine sensor telemetry"""
    return f"factory/{FACTORY_SITE_ID}/machine/{machine_type}/{machine_id}/telemetry"

def get_machine_command_topic(machine_type, machine_id):
    """Get MQTT topic for machine commands"""
    return f"factory/{FACTORY_SITE_ID}/machine/{machine_type}/{machine_id}/command"

def get_production_status_topic(order_id, step_name=None):
    """Get MQTT topic for production status"""
    if step_name:
        return f"factory/{FACTORY_SITE_ID}/production/{order_id}/step/{step_name}/status"
    return f"factory/{FACTORY_SITE_ID}/production/{order_id}/status"

def get_production_result_topic(order_id):
    """Get MQTT topic for production results"""
    return f"factory/{FACTORY_SITE_ID}/production/{order_id}/result"

# Legacy topics for backward compatibility
MQTT_TOPIC_MACHINE = "machine/data"
MQTT_TOPIC_PRODUCTION = "production/data"

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "factory_db")
DB_USER = os.getenv("DB_USER", "factory_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "factory_pass")

# TimescaleDB Configuration
TIMESCALE_HOST = os.getenv("TIMESCALE_HOST", "timescaledb")
TIMESCALE_PORT = int(os.getenv("TIMESCALE_PORT", 5432))
TIMESCALE_DB = os.getenv("TIMESCALE_DB", "factory_timeseries")
TIMESCALE_USER = os.getenv("TIMESCALE_USER", "factory_user")
TIMESCALE_PASSWORD = os.getenv("TIMESCALE_PASSWORD", "factory_pass")

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Production Configuration
PRODUCTION_SUCCESS_RATE = float(os.getenv("PRODUCTION_SUCCESS_RATE", 0.99))
PRODUCTION_LOOP_INTERVAL = int(os.getenv("PRODUCTION_LOOP_INTERVAL", 5))

# Machine Configuration
MACHINE_DATA_PUBLISH_INTERVAL = int(os.getenv("MACHINE_DATA_PUBLISH_INTERVAL", 5))
MACHINE_SENSOR_UPDATE_INTERVAL = int(os.getenv("MACHINE_SENSOR_UPDATE_INTERVAL", 2))

# Service Configuration
SERVICE_NAME = os.getenv("SERVICE_NAME", "unknown-service")
MACHINE_ID = os.getenv("MACHINE_ID", None)
MACHINE_TYPE = os.getenv("MACHINE_TYPE", None)

# Health Check Configuration
HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", 30))
