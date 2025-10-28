"""
Production Orchestrator Service
Coordinates production workflow across machines
"""
import sys
import os
import time
import logging
import signal
import json
from uuid import uuid4
from queue import Queue
from threading import Thread, Lock

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../shared'))

from mqtt_client import MQTTClient
from config import (
    MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE,
    FACTORY_SITE_ID, PRODUCTION_LOOP_INTERVAL,
    PRODUCTION_SUCCESS_RATE,
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, # ADD regular DB config
    get_machine_command_topic, get_production_status_topic,
    get_production_result_topic
)

from db import DatabaseConnection # ADD DatabaseConnection
from cloud_publisher import CloudPublisher # ADD CloudPublisher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
running = True
db_conn = None
cloud_publisher = None

production_queue = Queue()
active_orders = {}
active_orders_lock = Lock()


class ProductionOrder:
    """Represents a production order"""

    def __init__(self, product_name, product_details):
        self.order_id = str(uuid4())
        self.product_name = product_name
        self.product_details = self._process_product_details(product_details or {})
        self.status = "pending"
        self.steps = []
        self.current_step = 0
        self.created_at = time.time()
        self.completed_at = None

    def _process_product_details(self, details):
        """Fill in missing product details with defaults"""
        import random

        defaults = {
            "material": random.choice(["Cotton", "Denim", "Polyester"]),
            "cut_size": random.choice(["Small", "Medium", "Large", "X-Large"]),
            "stitch_type": random.choice(["Straight", "Zigzag", "Satin"]),
            "thread_color": random.choice(["Red", "Green", "Blue", "Black", "White"]),
            "iron_temperature_setpoint": random.randint(100, 180),
            "steam_level": random.choice(["Low", "Medium", "High"]),
            "ink_type": random.choice(["Water-based", "Plastisol", "None"])
        }

        for key, value in defaults.items():
            if key not in details or not details[key]:
                details[key] = value

        return details

    def to_dict(self):
        """Convert order to dictionary"""
        return {
            "order_id": self.order_id,
            "product_name": self.product_name,
            "product_details": self.product_details,
            "status": self.status,
            "steps": self.steps,
            "created_at": self.created_at,
            "completed_at": self.completed_at
        }


class ProductionOrchestrator:
    """Orchestrates production across multiple machines"""

    def __init__(self, mqtt_client):
        self.mqtt_client = mqtt_client
        self.production_steps = [
            {"name": "cutting", "machine_type": "cutting"},
            {"name": "sewing", "machine_type": "sewing"},
            {"name": "ironing", "machine_type": "ironing"},
            {"name": "printing", "machine_type": "printing"}
        ]
        self.machine_ids = {}  # machine_type -> machine_id mapping
        self.step_responses = {}  # order_id -> {step_name: response}
        self.failure_rate = 1 - PRODUCTION_SUCCESS_RATE

    def register_machine(self, machine_type, machine_id):
        """Register a machine for production"""
        self.machine_ids[machine_type] = machine_id
        logger.info(f"Registered {machine_type} machine: {machine_id}")

    def process_order(self, order: ProductionOrder):
        """Process a production order through all steps"""
        logger.info(f"Starting production order: {order.order_id}")
        global cloud_publisher

        order.status = "in_progress"

          # PERSIST & FORWARD: Initial status
        self._persist_order(order)
        cloud_publisher.publish_production_event(order.order_id, order.to_dict())

        # Publish initial status
        status_topic = get_production_status_topic(order.order_id)
        self.mqtt_client.publish_json(status_topic, {
            "order_id": order.order_id,
            "status": "in_progress",
            "current_step": 0,
            "total_steps": len(self.production_steps),
            "timestamp": time.time()
        })

        try:
            for idx, step_config in enumerate(self.production_steps):
                step_name = step_config["name"]
                machine_type = step_config["machine_type"]

                logger.info(f"[Order {order.order_id}] Step {idx + 1}/{len(self.production_steps)}: {step_name}")

                # Get machine ID for this step
                machine_id = self.machine_ids.get(machine_type)
                if not machine_id:
                    raise Exception(f"No machine registered for type: {machine_type}")

                # Prepare process data for this step
                process_data = self._get_process_data_for_step(step_name, order.product_details)

                # Execute step
                step_result = self._execute_step(order.order_id, step_name, machine_type,
                                                machine_id, process_data)

                # Record step result
                order.steps.append(step_result)

                # PERSIST & FORWARD: Step result
                self._persist_step(order.order_id, step_result)
                cloud_publisher.publish_production_event(order.order_id, step_result)

                # Publish step status
                step_status_topic = get_production_status_topic(order.order_id, step_name)
                self.mqtt_client.publish_json(step_status_topic, step_result)

                if step_result["status"] == "failed":
                    order.status = "failed"
                    logger.warning(f"[Order {order.order_id}] Failed at step: {step_name}")
                    break

            # If all steps succeeded
            if order.status != "failed":
                order.status = "completed"
                logger.info(f"[Order {order.order_id}] Completed successfully")

        except Exception as e:
            order.status = "failed"
            logger.error(f"[Order {order.order_id}] Error: {e}")
            order.steps.append({
                "name": "error",
                "status": "failed",
                "error": str(e),
                "timestamp": time.time()
            })

        finally:
            order.completed_at = time.time()
            # PERSIST & FORWARD: Final result
            self._persist_order(order)
            cloud_publisher.publish_production_event(order.order_id, order.to_dict())
            # Publish final result
            result_topic = get_production_result_topic(order.order_id)
            self.mqtt_client.publish_json(result_topic, order.to_dict())

            # Publish final status
            status_topic = get_production_status_topic(order.order_id)
            self.mqtt_client.publish_json(status_topic, {
                "order_id": order.order_id,
                "status": order.status,
                "timestamp": time.time()
            })

    def _persist_order(self, order: ProductionOrder):
        """Persist/Update the overall production order in PostgreSQL."""
        if not db_conn or not db_conn.connection:
            logger.error("DB connection unavailable, skipping order persistence.")
            return

        try:
            with db_conn.get_cursor() as cursor:
                # Use INSERT ON CONFLICT to handle initial creation and subsequent updates
                cursor.execute("""
                    INSERT INTO production_orders 
                    (order_id, product_name, product_details, status, completed_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (order_id) DO UPDATE SET 
                        status = EXCLUDED.status, 
                        product_details = EXCLUDED.product_details,
                        completed_at = EXCLUDED.completed_at,
                        updated_at = NOW()
                """, (
                    order.order_id, order.product_name, json.dumps(order.product_details), 
                    order.status, order.completed_at
                ))
            logger.debug(f"Order {order.order_id} persisted/updated.")
        except Exception as e:
            logger.error(f"Failed to persist order {order.order_id}: {e}")

    def _persist_step(self, order_id: str, step_result: dict):
        """Persist a single production step result in PostgreSQL."""
        if not db_conn or not db_conn.connection:
            logger.error("DB connection unavailable, skipping step persistence.")
            return
            
        try:
            with db_conn.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO production_steps 
                    (order_id, step_name, machine_id, status, process_data, completed_at, error_message)
                    VALUES (%s, %s, %s, %s, %s, NOW(), %s)
                """, (
                    order_id, 
                    step_result.get('name'), 
                    step_result.get('machine_id'), 
                    step_result.get('status'), 
                    json.dumps(step_result.get('process_data', {})), 
                    step_result.get('error')
                ))
            logger.debug(f"Step {step_result.get('name')} for order {order_id} persisted.")
        except Exception as e:
            logger.error(f"Failed to persist step for order {order_id}: {e}")

    def _get_process_data_for_step(self, step_name, product_details):
        """Extract relevant process data for a specific step"""
        if step_name == "cutting":
            return {
                "material": product_details["material"],
                "cut_size": product_details["cut_size"]
            }
        elif step_name == "sewing":
            return {
                "stitch_type": product_details["stitch_type"],
                "thread_color": product_details["thread_color"]
            }
        elif step_name == "ironing":
            return {
                "iron_temperature_setpoint": product_details["iron_temperature_setpoint"],
                "steam_level": product_details["steam_level"]
            }
        elif step_name == "printing":
            return {
                "ink_type": product_details["ink_type"]
            }
        return {}

    def _execute_step(self, order_id, step_name, machine_type, machine_id, process_data):
        """Execute a production step on a machine"""
        try:
            # Send command to machine via MQTT
            command_topic = get_machine_command_topic(machine_type, machine_id)
            response_topic = f"factory/{FACTORY_SITE_ID}/production/{order_id}/step/{step_name}/response"

            command = {
                "command": "process",
                "process_data": process_data,
                "order_id": order_id,
                "response_topic": response_topic
            }

            # Subscribe to response topic (this would need proper implementation)
            # For now, we'll simulate the execution
            self.mqtt_client.publish_json(command_topic, command)

            # Simulate processing time
            time.sleep(5)

            # Simulate success/failure
            import random
            random_value = random.uniform(0, 1)
            if random_value < self.failure_rate:
                return {
                    "name": step_name,
                    "machine_id": machine_id,
                    "status": "failed",
                    "process_data": process_data,
                    "error": "Machine operation failed",
                    "timestamp": time.time()
                }
            else:
                return {
                    "name": step_name,
                    "machine_id": machine_id,
                    "status": "success",
                    "process_data": process_data,
                    "timestamp": time.time()
                }

        except Exception as e:
            return {
                "name": step_name,
                "status": "failed",
                "error": str(e),
                "timestamp": time.time()
            }


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    global running
    logger.info("Shutdown signal received, stopping orchestrator...")
    running = False


def process_production_queue(orchestrator):
    """Process production orders from the queue"""
    global running

    while running:
        try:
            if not production_queue.empty():
                order = production_queue.get()
                with active_orders_lock:
                    active_orders[order.order_id] = order

                orchestrator.process_order(order)

                with active_orders_lock:
                    if order.order_id in active_orders:
                        del active_orders[order.order_id]

            time.sleep(PRODUCTION_LOOP_INTERVAL)
        except Exception as e:
            logger.error(f"Error processing production queue: {e}")


def handle_production_request(topic, payload):
    """Handle incoming production requests"""
    try:
        request = json.loads(payload)
        product_name = request.get("product_name")
        product_details = request.get("product_details")

        if product_name:
            order = ProductionOrder(product_name, product_details)
            production_queue.put(order)
            logger.info(f"Added production order to queue: {order.order_id}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in production request: {e}")
    except Exception as e:
        logger.error(f"Error handling production request: {e}")


def main():
    """Main service loop"""
    global running, db_conn, cloud_publisher

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Starting Production Orchestrator Service")

    # 1. Initialize Regular Database (PostgreSQL) Connection
    db_conn = DatabaseConnection(
        host=DB_HOST, port=DB_PORT, database=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )
    if not db_conn.connect():
        logger.error("Failed to connect to PostgreSQL, exiting...")
        return
    db_conn.initialize_schema() # Ensure tables are ready

    # Initialize MQTT client
    mqtt_client = MQTTClient(
        client_id="production-orchestrator",
        broker=MQTT_BROKER,
        port=MQTT_PORT,
        keepalive=MQTT_KEEPALIVE
    )

    # Connect to MQTT broker
    if not mqtt_client.connect():
        logger.error("Failed to connect to MQTT broker, exiting...")
        return

            
    # 3. Initialize Cloud Publisher
    cloud_publisher = CloudPublisher(mqtt_client, FACTORY_SITE_ID)

    # Initialize orchestrator
    orchestrator = ProductionOrchestrator(mqtt_client)

    # Register known machines (in real implementation, machines would register themselves)
    orchestrator.register_machine("cutting", "cutting-01")
    orchestrator.register_machine("sewing", "sewing-01")
    orchestrator.register_machine("ironing", "ironing-01")
    orchestrator.register_machine("printing", "printing-01")

    # Subscribe to production request topic
    request_topic = f"factory/{FACTORY_SITE_ID}/production/request"
    mqtt_client.subscribe(request_topic, handle_production_request)

    # Start MQTT loop
    mqtt_client.loop_start()

    logger.info(f"Production orchestrator is running...")
    logger.info(f"Listening for production requests on: {request_topic}")

    # Start production queue processor in a separate thread
    queue_thread = Thread(target=process_production_queue, args=(orchestrator,), daemon=True)
    queue_thread.start()

    # Main loop
    try:
        while running:
            time.sleep(1)
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        # Cleanup
        logger.info("Shutting down...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        db_conn.disconnect() # ADD disconnect for regular DB

        logger.info("Production orchestrator stopped")


if __name__ == "__main__":
    main()
