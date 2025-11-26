"""
Factory Monitoring Service
Listens to all machine data, logs it, stores it, and provides a command interface
for controlling machines.
"""
import sys
import os
import time
import logging
import signal
import json
from threading import Lock

# Add shared modules to path
sys.path.insert(0, '/app/shared')

from mqtt_client import MQTTClientWrapper
from database import TimeSeriesConnection, DatabaseConnection
from cloud_publisher import CloudPublisher
from config import (
    MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE,
    FACTORY_SITE_ID,
    TIMESCALE_HOST, TIMESCALE_PORT, TIMESCALE_DB, TIMESCALE_USER, TIMESCALE_PASSWORD,
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
    get_machine_command_topic
)

# Get factory ID from environment (for machine topic path)
import os
FACTORY_ID = os.getenv("FACTORY_ID", "tshirt-factory-001")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Global Variables ---
running = True
active_machines = {}
active_machines_lock = Lock()
mqtt_client = None
ts_conn = None
db_conn = None
cloud_publisher = None


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    global running
    logger.info("Shutdown signal received, stopping monitoring service...")
    running = False


def insert_telemetry_to_db(machine_id, machine_type, telemetry_data):
    """Insert telemetry data into TimescaleDB (primary) or PostgreSQL (fallback)."""
    global ts_conn, db_conn
    
    # Try TimescaleDB first (preferred for time-series)
    if ts_conn and ts_conn.connection:
        try:
            sensor_data = telemetry_data.get("sensor_data", {})
            runtime_state = telemetry_data.get("runtime_state", "unknown")
            ts_conn.insert_sensor_data(machine_id, machine_type, sensor_data, runtime_state)
            logger.debug(f"Telemetry for {machine_id} inserted into TimescaleDB")
            return
        except Exception as e:
            logger.debug(f"TimescaleDB insert failed: {e}, falling back to PostgreSQL")
    
    # Fall back to PostgreSQL
    if db_conn and db_conn.connection:
        try:
            runtime_state = telemetry_data.get("runtime_state", "unknown")
            sensor_data = telemetry_data.get("sensor_data", {})
            telemetry_json = json.dumps(sensor_data, ensure_ascii=False)
            
            with db_conn.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO machine_telemetry (machine_id, machine_type, sensor_data, runtime_state)
                    VALUES (%s, %s, %s, %s)
                """, (machine_id, machine_type, telemetry_json, runtime_state))
            logger.debug(f"Telemetry for {machine_id} inserted into PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to insert telemetry for {machine_id}: {e}")


def check_machine_health(machine_id, status_data):
    """Perform simple health checks on incoming machine status data."""
    runtime_state = status_data.get("runtime_state")
    if runtime_state == "error":
        logger.warning(
            f"ALERT: Machine {machine_id} has reported an 'error' state! "
            f"Total Ops: {status_data.get('total_operations')}, "
            f"Failed Ops: {status_data.get('failed_operations')}"
        )


def handle_machine_message(topic, payload):
    """
    Callback for processing messages from all machine topics.
    Now persists data locally AND forwards to the cloud.
    """
    global cloud_publisher
    logger.info(f"✓ handle_machine_message INVOKED - topic: {topic}")
    try:
        parts = topic.split('/')
        # Expected: factory/{factory_id}/machines/{machine_id}/{data_type}
        if len(parts) != 5:
            logger.warning(f"⚠ Invalid topic format (expected 5 parts, got {len(parts)}): {topic}")
            return

        factory_id = parts[1]
        machine_id = parts[3]
        data_type = parts[4] # "status" or "telemetry"

        logger.info(f"✓ Parsing message: factory={factory_id}, machine={machine_id}, type={data_type}")
        data = json.loads(payload)
        
        with active_machines_lock:
            # If this is the first time we see this machine, initialize its entry
            if machine_id not in active_machines:
                active_machines[machine_id] = {"machine_type": machine_id.rsplit('-', 1)[0]}  # Extract type from ID
                logger.info(f"Discovered new machine: {machine_id}")

            # Update the machine's state
            active_machines[machine_id][f'last_{data_type}'] = data
            active_machines[machine_id]['last_seen'] = time.time()

        if data_type == "status":
            logger.info(f"Received STATUS from {machine_id}: State = {data.get('runtime_state')}")
            check_machine_health(machine_id, data)
            
            # 1. PERSIST (PostgreSQL)
            insert_status_to_db(machine_id, data)
            
            # 2. FORWARD (Cloud)
            cloud_publisher.publish_telemetry(machine_id, data)

        elif data_type == "telemetry":
            logger.info(f"Received TELEMETRY from {machine_id}")
            
            # Extract machine type from data or active_machines
            with active_machines_lock:
                machine_type = active_machines.get(machine_id, {}).get('machine_type', 'unknown')
            
            # 1. PERSIST (TimescaleDB)
            insert_telemetry_to_db(machine_id, machine_type, data)
            
            # 2. FORWARD (Cloud)
            cloud_publisher.publish_telemetry(machine_id, data)

    except json.JSONDecodeError:
        logger.error(f"Invalid JSON received on topic {topic}")
    except Exception as e:
        logger.error(f"Error in handle_machine_message: {e}")


def handle_monitoring_command(topic, payload):
    """
    Handles incoming commands for the monitoring service itself.
    e.g., to tell it to start/stop a specific machine.
    """
    global mqtt_client
    try:
        command = json.loads(payload)
        command_type = command.get("command")
        machine_id = command.get("machine_id")

        if not command_type or not machine_id:
            logger.error(f"Received invalid command: {payload}")
            return

        logger.info(f"Received command '{command_type}' for machine '{machine_id}'")

        with active_machines_lock:
            machine_info = active_machines.get(machine_id)

        if not machine_info:
            logger.error(f"Cannot execute command. Machine '{machine_id}' is unknown.")
            return

        machine_type = machine_info.get("machine_type")
        command_topic = get_machine_command_topic(machine_type, machine_id)
        cmd_payload = {}

        if command_type == "stop_machine":
            cmd_payload = {"command": "stop"}
            mqtt_client.publish_json(command_topic, cmd_payload)
            logger.info(f"Sent 'stop' command to {machine_id} on topic {command_topic}")

        elif command_type == "start_machine":
            cmd_payload = {"command": "start"}
            mqtt_client.publish_json(command_topic, cmd_payload)
            logger.info(f"Sent 'start' command to {machine_id} on topic {command_topic}")

        elif command_type == "set_failure_rate":
            rate = command.get("rate")
            if rate is not None:
                cmd_payload = {"command": "set_failure_rate", "rate": float(rate)}
                mqtt_client.publish_json(command_topic, cmd_payload)
                logger.info(f"Sent 'set_failure_rate={rate}' command to {machine_id}")
            else:
                logger.error("'set_failure_rate' command requires a 'rate' parameter.")
        else:
            logger.warning(f"Unknown command type: {command_type}")

    except Exception as e:
        logger.error(f"Error handling monitoring command: {e}")


def main():
    """Main service loop"""
    global running, mqtt_client, ts_conn, db_conn, cloud_publisher

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Starting Factory Monitoring Service")

    # 1. Initialize Regular Database (PostgreSQL) Connection
    db_conn = DatabaseConnection(
        host=DB_HOST, port=DB_PORT, database=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )
    if not db_conn.connect():
        logger.error("Failed to connect to PostgreSQL, exiting...")
        return
    db_conn.initialize_schema() # Ensure tables are ready

    # 2. Initialize TimescaleDB Connection (for time-series data)
    ts_conn = TimeSeriesConnection(
        host=TIMESCALE_HOST, port=TIMESCALE_PORT, database=TIMESCALE_DB,
        user=TIMESCALE_USER, password=TIMESCALE_PASSWORD
    )
    if not ts_conn.connect():
        logger.warning("Failed to connect to TimescaleDB, will use PostgreSQL for telemetry")
        ts_conn = None
    else:
        ts_conn.initialize_schema()
        logger.info("Connected to TimescaleDB for time-series data")

    # Initialize MQTT client
    mqtt_client = MQTTClientWrapper(
        client_id="factory-monitoring-service",
        broker=MQTT_BROKER, port=MQTT_PORT, keepalive=MQTT_KEEPALIVE
    )
    if not mqtt_client.connect():
        logger.error("Failed to connect to MQTT broker, exiting...")
        return

    # 4. Initialize Cloud Publisher
    cloud_publisher = CloudPublisher(mqtt_client, FACTORY_SITE_ID)

    # Subscribe to all machine status and telemetry topics using a wildcard
    # Topic pattern: factory/{factory_id}/machines/{machine_id}/{status|telemetry}
    machine_data_topic = f"factory/{FACTORY_ID}/machines/+/+"
    mqtt_client.subscribe(machine_data_topic, handle_machine_message)
    logger.info(f"Subscribed to machine data on topic: {machine_data_topic}")

    # Subscribe to the monitoring service's own command topic
    monitoring_command_topic = f"factory/{FACTORY_SITE_ID}/monitoring/command"
    mqtt_client.subscribe(monitoring_command_topic, handle_monitoring_command)
    logger.info(f"Listening for commands on topic: {monitoring_command_topic}")

    # Start the MQTT client loop in a background thread
    mqtt_client.loop_start()

    try:
        while running:
            # The main loop can be used for periodic tasks, e.g., checking for offline machines
            time.sleep(1)
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        # Cleanup
        logger.info("Shutting down...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        ts_conn.disconnect()
        db_conn.disconnect() # ADD disconnect for regular DB
        logger.info("Monitoring service stopped")


def insert_status_to_db(machine_id, status_data):
    """Insert machine status log into PostgreSQL."""
    if not db_conn or not db_conn.connection:
        logger.error("PostgreSQL connection is not available. Cannot insert status log.")
        return
    
    # Extract relevant fields for the machine_status_log table defined in db.py
    runtime_state = status_data.get("runtime_state")
    total_operations = status_data.get("total_operations", 0)
    failed_operations = status_data.get("failed_operations", 0)

    try:
        with db_conn.get_cursor() as cursor:
            # First, ensure machine is registered (optional, but good practice)
            cursor.execute("""
                INSERT INTO machines (machine_id, machine_type, machine_name)
                VALUES (%s, %s, %s)
                ON CONFLICT (machine_id) DO UPDATE SET updated_at = NOW()
            """, (machine_id, status_data.get("machine_type"), status_data.get("machine_name")))

            # Insert into status log
            cursor.execute("""
                INSERT INTO machine_status_log 
                (machine_id, runtime_state, total_operations, failed_operations)
                VALUES (%s, %s, %s, %s)
            """, (machine_id, runtime_state, total_operations, failed_operations))
        logger.debug(f"Successfully logged status for {machine_id} to PostgreSQL.")
    except Exception as e:
        logger.error(f"Failed to insert status log for {machine_id}: {e}")

if __name__ == "__main__":
    main()