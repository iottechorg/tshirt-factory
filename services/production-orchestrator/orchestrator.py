"""
Production Orchestrator V2 - Workflow-based orchestration
Supports flexible, configurable production workflows
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
from typing import Dict, List, Optional

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), './shared'))

from mqtt_client import MQTTClient
from workflow_engine import WorkflowRegistry, WorkflowDefinition, WorkflowStep, WorkflowValidator
from config import (
    MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE,
    FACTORY_SITE_ID, PRODUCTION_LOOP_INTERVAL,
    get_machine_command_topic, get_production_status_topic,
    get_production_result_topic
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
running = True
production_queue = Queue()
active_orders = {}
active_orders_lock = Lock()
machine_registry = {}  # machine_type -> [machine_ids]
machine_registry_lock = Lock()
machine_states = {}  # machine_id -> {status, current_order, last_update}
machine_states_lock = Lock()
machine_responses = {}  # response_topic -> response_data
machine_responses_lock = Lock()
machine_performance = {}  # machine_id -> {total_ops, failures, avg_time}
machine_performance_lock = Lock()


class ProductionOrder:
    """Represents a production order with workflow"""

    def __init__(self, product_name: str, workflow: WorkflowDefinition, product_details: Dict):
        self.order_id = str(uuid4())
        self.product_name = product_name
        self.workflow = workflow
        self.product_details = self._process_product_details(product_details)
        self.status = "pending"
        self.step_results = []  # List of completed step results
        self.current_step_index = 0
        self.created_at = time.time()
        self.completed_at = None
        self.workflow_state = {}  # Stores outputs from each step

    def _process_product_details(self, details: Dict) -> Dict:
        """Fill in missing product details with defaults"""
        import random

        defaults = {
            "material": random.choice(["Cotton", "Denim", "Polyester", "Fleece"]),
            "cut_size": random.choice(["Small", "Medium", "Large", "X-Large"]),
            "stitch_type": random.choice(["Straight", "Zigzag", "Satin"]),
            "thread_color": random.choice(["Red", "Green", "Blue", "Black", "White"]),
            "iron_temperature_setpoint": random.randint(100, 180),
            "steam_level": random.choice(["Low", "Medium", "High"]),
            "ink_type": random.choice(["Water-based", "Plastisol", "None"]),
            "design_name": random.choice(["Logo1", "Logo2", "Pattern1", "None"])
        }

        for key, value in defaults.items():
            if key not in details or not details[key]:
                details[key] = value

        return details

    def to_dict(self) -> Dict:
        """Convert order to dictionary"""
        return {
            "order_id": self.order_id,
            "product_name": self.product_name,
            "workflow_id": self.workflow.workflow_id,
            "workflow_name": self.workflow.workflow_name,
            "product_details": self.product_details,
            "status": self.status,
            "step_results": self.step_results,
            "current_step": self.current_step_index,
            "total_steps": len(self.workflow.steps),
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "workflow_state": self.workflow_state
        }


class WorkflowOrchestrator:
    """Orchestrates production using flexible workflows"""

    def __init__(self, mqtt_client: MQTTClient, workflow_registry: WorkflowRegistry):
        self.mqtt_client = mqtt_client
        self.workflow_registry = workflow_registry

    def get_available_machine(self, machine_type: str) -> Optional[str]:
        """Get an available machine of the specified type"""
        with machine_registry_lock:
            machines = machine_registry.get(machine_type, [])
            if not machines:
                return None

            # Find first available machine (not busy)
            with machine_states_lock:
                for machine_id in machines:
                    state = machine_states.get(machine_id, {})
                    if state.get("status") != "busy":
                        return machine_id

                # If all busy, return first one (will queue)
                return machines[0] if machines else None

    def process_order(self, order: ProductionOrder):
        """Process a production order through its workflow"""
        logger.info(f"Starting order {order.order_id} using workflow '{order.workflow.workflow_name}'")
        order.status = "in_progress"

        # Publish initial status
        self._publish_status(order, "started")

        try:
            # Process each step in the workflow
            for step_index, step in enumerate(order.workflow.steps):
                order.current_step_index = step_index

                logger.info(f"[Order {order.order_id}] Step {step_index + 1}/{len(order.workflow.steps)}: "
                           f"{step.operation} on {step.machine_type}")

                # Check if this step can run (inputs available)
                is_valid, errors = WorkflowValidator.validate_inputs(step, {
                    **order.product_details,
                    **order.workflow_state
                })

                if not is_valid:
                    raise Exception(f"Step validation failed: {errors}")

                # Get an available machine
                machine_id = self.get_available_machine(step.machine_type)
                if not machine_id:
                    raise Exception(f"No available machine of type: {step.machine_type}")

                # Execute the step
                step_result = self._execute_step(order, step, machine_id)

                # Store step result
                order.step_results.append(step_result)

                # Update workflow state with step outputs
                for output in step.outputs:
                    order.workflow_state[output] = True  # Mark as produced

                # Publish step result
                self._publish_step_result(order, step, step_result)

                # Check if step failed
                if step_result["status"] == "failed":
                    order.status = "failed"
                    logger.warning(f"[Order {order.order_id}] Failed at step: {step.operation}")
                    break

            # If all steps succeeded
            if order.status != "failed":
                order.status = "completed"
                logger.info(f"[Order {order.order_id}] Completed successfully")

        except Exception as e:
            order.status = "failed"
            logger.error(f"[Order {order.order_id}] Error: {e}")
            order.step_results.append({
                "step_id": "error",
                "status": "failed",
                "error": str(e),
                "timestamp": time.time()
            })

        finally:
            order.completed_at = time.time()

            # Publish final result
            self._publish_final_result(order)

    def _execute_step(self, order: ProductionOrder, step: WorkflowStep, machine_id: str) -> Dict:
        """Execute a single workflow step with retry logic"""
        max_retries = step.retry_count
        attempt = 0

        while attempt <= max_retries:
            try:
                if attempt > 0:
                    logger.info(f"[Order {order.order_id}] Retrying step {step.step_id}, attempt {attempt + 1}/{max_retries + 1}")

                # Extract process data for this step
                process_data = WorkflowValidator.extract_process_data(step, {
                    **order.product_details,
                    **order.workflow_state
                })

                # Add operation name
                process_data["operation"] = step.operation

                # Send command to machine
                command_topic = get_machine_command_topic(step.machine_type, machine_id)
                response_topic = f"factory/{FACTORY_SITE_ID}/production/{order.order_id}/step/{step.step_id}/response"

                command = {
                    "command": "process",
                    "process_data": process_data,
                    "order_id": order.order_id,
                    "step_id": step.step_id,
                    "response_topic": response_topic
                }

                # Mark machine as busy
                self._set_machine_state(machine_id, "busy", order.order_id)

                # Send command
                self.mqtt_client.publish_json(command_topic, command)
                logger.debug(f"[Order {order.order_id}] Sent command to {machine_id} on {command_topic}")

                # Wait for machine response
                start_time = time.time()
                result = self._wait_for_machine_response(response_topic, step.timeout_seconds)

                if result:
                    elapsed_time = time.time() - start_time

                    # Track performance
                    self._track_machine_performance(machine_id, elapsed_time, result.get("status") == "failed")

                    # Mark machine as available
                    self._set_machine_state(machine_id, "idle", None)

                    if result.get("status") == "success":
                        logger.info(f"[Order {order.order_id}] Step {step.step_id} completed in {elapsed_time:.2f}s")
                        return {
                            "step_id": step.step_id,
                            "operation": step.operation,
                            "machine_type": step.machine_type,
                            "machine_id": machine_id,
                            "status": "success",
                            "process_data": process_data,
                            "outputs": step.outputs,
                            "elapsed_time": elapsed_time,
                            "timestamp": time.time()
                        }
                    else:
                        # Machine reported failure
                        error_msg = result.get("error", "Machine operation failed")
                        logger.warning(f"[Order {order.order_id}] Step {step.step_id} failed: {error_msg}")

                        if attempt < max_retries:
                            attempt += 1
                            time.sleep(2)  # Brief delay before retry
                            continue
                        else:
                            return {
                                "step_id": step.step_id,
                                "operation": step.operation,
                                "machine_type": step.machine_type,
                                "machine_id": machine_id,
                                "status": "failed",
                                "process_data": process_data,
                                "error": error_msg,
                                "attempts": attempt + 1,
                                "timestamp": time.time()
                            }
                else:
                    # Timeout waiting for response
                    logger.error(f"[Order {order.order_id}] Timeout waiting for response from {machine_id}")
                    self._set_machine_state(machine_id, "error", None)

                    if attempt < max_retries:
                        attempt += 1
                        time.sleep(2)
                        continue
                    else:
                        return {
                            "step_id": step.step_id,
                            "operation": step.operation,
                            "machine_type": step.machine_type,
                            "machine_id": machine_id,
                            "status": "failed",
                            "error": f"Timeout waiting for machine response ({step.timeout_seconds}s)",
                            "attempts": attempt + 1,
                            "timestamp": time.time()
                        }

            except Exception as e:
                logger.error(f"[Order {order.order_id}] Error executing step: {e}")
                self._set_machine_state(machine_id, "error", None)

                if attempt < max_retries:
                    attempt += 1
                    time.sleep(2)
                    continue
                else:
                    return {
                        "step_id": step.step_id,
                        "operation": step.operation,
                        "status": "failed",
                        "error": str(e),
                        "attempts": attempt + 1,
                        "timestamp": time.time()
                    }

    def _wait_for_machine_response(self, response_topic: str, timeout_seconds: int) -> Optional[Dict]:
        """Wait for machine response on specified topic"""
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            with machine_responses_lock:
                if response_topic in machine_responses:
                    response = machine_responses.pop(response_topic)
                    return response

            time.sleep(0.1)  # Check every 100ms

        return None  # Timeout

    def _set_machine_state(self, machine_id: str, status: str, order_id: Optional[str]):
        """Update machine state"""
        with machine_states_lock:
            machine_states[machine_id] = {
                "status": status,
                "current_order": order_id,
                "last_update": time.time()
            }

    def _track_machine_performance(self, machine_id: str, elapsed_time: float, failed: bool):
        """Track machine performance metrics"""
        with machine_performance_lock:
            if machine_id not in machine_performance:
                machine_performance[machine_id] = {
                    "total_ops": 0,
                    "failures": 0,
                    "total_time": 0.0,
                    "avg_time": 0.0
                }

            perf = machine_performance[machine_id]
            perf["total_ops"] += 1
            if failed:
                perf["failures"] += 1
            perf["total_time"] += elapsed_time
            perf["avg_time"] = perf["total_time"] / perf["total_ops"]

    def _publish_status(self, order: ProductionOrder, event: str):
        """Publish order status update"""
        status_topic = get_production_status_topic(order.order_id)
        self.mqtt_client.publish_json(status_topic, {
            "order_id": order.order_id,
            "event": event,
            "status": order.status,
            "workflow": order.workflow.workflow_name,
            "current_step": order.current_step_index,
            "total_steps": len(order.workflow.steps),
            "timestamp": time.time()
        })

    def _publish_step_result(self, order: ProductionOrder, step: WorkflowStep, result: Dict):
        """Publish step execution result"""
        step_topic = get_production_status_topic(order.order_id, step.step_id)
        self.mqtt_client.publish_json(step_topic, result)

    def _publish_final_result(self, order: ProductionOrder):
        """Publish final production result"""
        result_topic = get_production_result_topic(order.order_id)
        self.mqtt_client.publish_json(result_topic, order.to_dict())


def register_machine(machine_type: str, machine_id: str):
    """Register a machine in the registry"""
    with machine_registry_lock:
        if machine_type not in machine_registry:
            machine_registry[machine_type] = []
        if machine_id not in machine_registry[machine_type]:
            machine_registry[machine_type].append(machine_id)
            logger.info(f"Registered machine: {machine_type}/{machine_id}")


def handle_machine_registration(topic: str, payload: str):
    """Handle machine registration messages"""
    try:
        data = json.loads(payload)
        machine_type = data.get("machine_type")
        machine_id = data.get("machine_id")

        if machine_type and machine_id:
            register_machine(machine_type, machine_id)
    except Exception as e:
        logger.error(f"Error handling machine registration: {e}")


def handle_machine_response(topic: str, payload: str):
    """Handle machine response messages"""
    try:
        response = json.loads(payload)

        # Store response in the responses dict
        with machine_responses_lock:
            machine_responses[topic] = response

        logger.debug(f"Received machine response on {topic}: {response.get('status')}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in machine response: {e}")
    except Exception as e:
        logger.error(f"Error handling machine response: {e}")


def handle_production_request(topic: str, payload: str):
    """Handle incoming production requests"""
    global workflow_registry

    try:
        request = json.loads(payload)
        product_name = request.get("product_name")
        workflow_id = request.get("workflow_id")
        product_type = request.get("product_type")
        product_details = request.get("product_details", {})

        # Determine which workflow to use
        workflow = None
        if workflow_id:
            workflow = workflow_registry.get(workflow_id)
        elif product_type:
            workflow = workflow_registry.get_by_product_type(product_type)
        else:
            # Default to standard t-shirt workflow
            workflow = workflow_registry.get("workflow-tshirt-standard")

        if not workflow:
            logger.error(f"Workflow not found: {workflow_id or product_type}")
            return

        # Create and queue order
        order = ProductionOrder(product_name, workflow, product_details)
        production_queue.put(order)

        logger.info(f"Queued order {order.order_id} with workflow '{workflow.workflow_name}'")

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in production request: {e}")
    except Exception as e:
        logger.error(f"Error handling production request: {e}")


def handle_workflow_adjustment(topic: str, payload: str):
    """Handle workflow adjustment requests"""
    global workflow_registry

    try:
        request = json.loads(payload)
        action = request.get("action")  # adjust_timeout, adjust_retry, etc.
        workflow_id = request.get("workflow_id")
        step_id = request.get("step_id")
        parameter = request.get("parameter")
        value = request.get("value")

        workflow = workflow_registry.get(workflow_id)
        if not workflow:
            logger.error(f"Workflow not found: {workflow_id}")
            return

        # Find the step
        step = next((s for s in workflow.steps if s.step_id == step_id), None)
        if not step:
            logger.error(f"Step not found: {step_id}")
            return

        # Apply adjustment
        if parameter == "timeout_seconds":
            step.timeout_seconds = int(value)
            logger.info(f"Adjusted {workflow_id}/{step_id} timeout to {value}s")
        elif parameter == "retry_count":
            step.retry_count = int(value)
            logger.info(f"Adjusted {workflow_id}/{step_id} retry count to {value}")
        else:
            logger.warning(f"Unknown parameter: {parameter}")

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in workflow adjustment: {e}")
    except Exception as e:
        logger.error(f"Error handling workflow adjustment: {e}")


def handle_performance_query(topic: str, payload: str):
    """Handle performance query requests"""
    try:
        request = json.loads(payload)
        response_topic = request.get("response_topic")

        if not response_topic:
            logger.warning("No response_topic in performance query")
            return

        # Gather performance data
        performance_data = {
            "machines": {},
            "timestamp": time.time()
        }

        with machine_performance_lock:
            for machine_id, perf in machine_performance.items():
                performance_data["machines"][machine_id] = {
                    "total_operations": perf["total_ops"],
                    "failures": perf["failures"],
                    "failure_rate": perf["failures"] / perf["total_ops"] if perf["total_ops"] > 0 else 0,
                    "average_time": perf["avg_time"]
                }

        # Publish response (would need mqtt_client reference - will handle in main)
        logger.info(f"Performance query: {len(performance_data['machines'])} machines")

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in performance query: {e}")
    except Exception as e:
        logger.error(f"Error handling performance query: {e}")


def process_production_queue(orchestrator: WorkflowOrchestrator):
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


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    global running
    logger.info("Shutdown signal received, stopping orchestrator...")
    running = False


def load_workflows_from_directory(registry: WorkflowRegistry, directory: str):
    """Load workflow definitions from JSON files"""
    import glob
    workflow_files = glob.glob(os.path.join(directory, "*.json"))

    loaded_count = 0
    for file_path in workflow_files:
        try:
            registry.load_from_file(file_path)
            loaded_count += 1
        except Exception as e:
            logger.warning(f"Failed to load workflow from {file_path}: {e}")

    return loaded_count


def main():
    """Main service loop"""
    global running, workflow_registry

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Starting Production Orchestrator V2 (Workflow-based)")

    # Initialize workflow registry
    workflow_registry = WorkflowRegistry()

    # Load workflows from JSON files
    workflows_dir = os.path.join(os.path.dirname(__file__), "../../workflows")
    if os.path.exists(workflows_dir):
        loaded = load_workflows_from_directory(workflow_registry, workflows_dir)
        logger.info(f"Loaded {loaded} workflow(s) from {workflows_dir}")

    logger.info(f"Total workflows available: {len(workflow_registry.list_all())}")
    for workflow in workflow_registry.list_all():
        logger.info(f"  - {workflow.workflow_name} ({workflow.product_type}) - {len(workflow.steps)} steps")

    # Initialize MQTT client
    mqtt_client = MQTTClient(
        client_id="production-orchestrator-v2",
        broker=MQTT_BROKER,
        port=MQTT_PORT,
        keepalive=MQTT_KEEPALIVE
    )

    # Connect to MQTT broker
    if not mqtt_client.connect():
        logger.error("Failed to connect to MQTT broker, exiting...")
        return

    # Initialize orchestrator
    orchestrator = WorkflowOrchestrator(mqtt_client, workflow_registry)

    # Register default machines (in real system, machines register themselves)
    register_machine("cutting", "cutting-01")
    register_machine("sewing", "sewing-01")
    register_machine("ironing", "ironing-01")
    register_machine("printing", "printing-01")
    register_machine("qualitycheck", "qualitycheck-01")
    register_machine("folding", "folding-01")
    register_machine("packaging", "packaging-01")

    # Subscribe to topics
    request_topic = f"factory/{FACTORY_SITE_ID}/production/request"
    registration_topic = f"factory/{FACTORY_SITE_ID}/machine/+/+/register"
    response_topic = f"factory/{FACTORY_SITE_ID}/production/+/step/+/response"
    workflow_adjust_topic = f"factory/{FACTORY_SITE_ID}/orchestrator/workflow/adjust"
    performance_topic = f"factory/{FACTORY_SITE_ID}/orchestrator/performance/query"

    mqtt_client.subscribe(request_topic, handle_production_request)
    mqtt_client.subscribe(registration_topic, handle_machine_registration)
    mqtt_client.subscribe(response_topic, handle_machine_response)
    mqtt_client.subscribe(workflow_adjust_topic, handle_workflow_adjustment)
    mqtt_client.subscribe(performance_topic, handle_performance_query)

    # Start MQTT loop
    mqtt_client.loop_start()

    logger.info(f"Orchestrator is running...")
    logger.info(f"Listening for production requests on: {request_topic}")
    logger.info(f"Available product types: {', '.join(workflow_registry.list_product_types())}")

    # Start production queue processor
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
        logger.info("Production orchestrator stopped")


if __name__ == "__main__":
    main()
