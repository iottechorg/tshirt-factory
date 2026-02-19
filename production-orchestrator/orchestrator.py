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
sys.path.insert(0, '/app/shared')

from mqtt_client import MQTTClientWrapper
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
orchestrator_instance = None


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

    def __init__(self, mqtt_client: MQTTClientWrapper, workflow_registry: WorkflowRegistry):
        self.mqtt_client = mqtt_client
        self.workflow_registry = workflow_registry

    def get_available_machine(self, machine_type: str) -> Optional[str]:
        """Get an available machine of the specified type (simple round-robin for now)"""
        with machine_registry_lock:
            machines = machine_registry.get(machine_type, [])
            if machines:
                # Simple: return first available (in real system, check machine status)
                return machines[0]
            return None

    def _execute_step_with_retry(self, order: ProductionOrder, step: WorkflowStep) -> Dict:
        """Execute a step with retry logic based on step configuration"""
        # Get retry configuration
        retry_config = step.retry if isinstance(step.retry, dict) else {}
        max_attempts = retry_config.get('max_attempts', 1) if retry_config.get('enabled', False) else 1
        delay_seconds = retry_config.get('delay_seconds', 0)
        
        attempt = 0
        last_result = None
        
        while attempt < max_attempts:
            attempt += 1
            
            # Get an available machine
            machine_id = self.get_available_machine(step.machine_type)
            if not machine_id:
                raise Exception(f"No available machine of type: {step.machine_type}")
            
            logger.info(f"[Order {order.order_id}] Executing step '{step.step_name or step.step_id}' (attempt {attempt}/{max_attempts})")
            
            # Execute the step
            last_result = self._execute_step(order, step, machine_id)
            
            # If successful, update workflow state and return
            if last_result["status"] == "success":
                # Update workflow state with step outputs
                for output in step.outputs:
                    order.workflow_state[output] = True  # Mark as produced
                return last_result
            
            # If failed and we have retries left, wait before retrying
            if attempt < max_attempts:
                logger.warning(f"[Order {order.order_id}] Step failed, retrying after {delay_seconds}s...")
                time.sleep(delay_seconds)
        
        # If we exhausted all retries, return the last failed result
        return last_result

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
                           f"{step.step_name or step.operation} on {step.machine_type}")

                # Check if this step can run (inputs available)
                is_first_step = (step_index == 0)
                is_valid, errors = WorkflowValidator.validate_inputs(
                    step, 
                    {**order.product_details, **order.workflow_state},
                    is_first_step=is_first_step
                )

                if not is_valid:
                    raise Exception(f"Step validation failed: {errors}")

                # Execute step with retry logic
                step_result = self._execute_step_with_retry(order, step)

                # Store step result
                order.step_results.append(step_result)

                # Publish step result
                self._publish_step_result(order, step, step_result)

                # Check if step failed after all retries
                if step_result["status"] == "failed":
                    # Check for quality conditions
                    should_fail = True
                    for condition in step.conditions:
                        if condition.get('type') == 'quality' and condition.get('on_failure') == 'reject':
                            logger.error(f"[Order {order.order_id}] Quality condition failed, rejecting order")
                            should_fail = True
                            break
                    
                    if should_fail:
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
                "operation": "error",
                "status": "failed",
                "error": str(e),
                "timestamp": time.time()
            })

        finally:
            order.completed_at = time.time()

            # Publish final result
            self._publish_final_result(order)

    def _execute_step(self, order: ProductionOrder, step: WorkflowStep, machine_id: str) -> Dict:
        """Execute a single workflow step"""
        try:
            # Extract process data for this step from product details and workflow state
            process_data = WorkflowValidator.extract_process_data(step, {
                **order.product_details,
                **order.workflow_state
            })

            # Add step-specific parameters to process data
            if step.parameters:
                process_data.update(step.parameters)

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
                "step_name": step.step_name,
                "timeout_seconds": step.timeout_seconds,
                "retry": step.retry,
                "response_topic": response_topic
            }

            logger.info(f"[Order {order.order_id}] Executing step '{step.step_name or step.step_id}' "
                       f"on machine {machine_id} with params: {step.parameters}")
            
            self.mqtt_client.publish_json(command_topic, command)

            # Simulate processing time (in real system, wait for machine response)
            time.sleep(5)

            # Simulate success/failure
            import random
            random_value = random.uniform(0, 1)
            
            # Use global production success rate if available, otherwise default
            from config import PRODUCTION_SUCCESS_RATE
            success_rate = getattr(self, 'production_success_rate', PRODUCTION_SUCCESS_RATE)
            failure_rate = 1.0 - success_rate

            if random_value < failure_rate:
                # Check if step has retry configuration
                should_retry = False
                retry_config = step.retry
                if isinstance(retry_config, dict) and retry_config.get('enabled'):
                    should_retry = True
                
                return {
                    "step_id": step.step_id,
                    "operation": step.operation,
                    "machine_type": step.machine_type,
                    "machine_id": machine_id,
                    "status": "failed",
                    "process_data": process_data,
                    "should_retry": should_retry,
                    "error": f"Machine operation failed for {step.operation}",
                    "timestamp": time.time()
                }
            else:
                return {
                    "step_id": step.step_id,
                    "step_name": step.step_name,
                    "operation": step.operation,
                    "machine_type": step.machine_type,
                    "machine_id": machine_id,
                    "status": "success",
                    "process_data": process_data,
                    "outputs": step.outputs,
                    "timestamp": time.time()
                }

        except Exception as e:
            return {
                "step_id": step.step_id,
                "operation": step.operation,
                "status": "failed",
                "error": str(e),
                "timestamp": time.time()
            }

    def _publish_status(self, order: ProductionOrder, event: str):
        """Publish order status update"""
        status_topic = get_production_status_topic(order.order_id)
        self.mqtt_client.publish_json(status_topic, {
            "order_id": order.order_id,
            "product_name": order.product_name,
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


def load_machines_from_config(factory_config_path: str):
    """Load machines from factory configuration file"""
    global machine_registry
    try:
        logger.info(f"Attempting to load machines from: {factory_config_path}")
        logger.info(f"File exists: {os.path.exists(factory_config_path)}")
        
        with open(factory_config_path, 'r') as f:
            config = json.load(f)
        
        machines = config.get('machines', [])
        logger.info(f"Found {len(machines)} machines in factory config")
        
        for machine in machines:
            if machine.get('enabled', True):
                machine_type = machine.get('machine_type')
                machine_id = machine.get('machine_id')
                if machine_type and machine_id:
                    register_machine(machine_type, machine_id)
                else:
                    logger.warning(f"Skipping machine with incomplete data: {machine}")
            else:
                logger.info(f"Skipping disabled machine: {machine.get('machine_id')}")
        
        logger.info(f"✓ Machine registry initialized with {len(machine_registry)} types: {dict(machine_registry)}")
        
        if not machine_registry:
            logger.error("WARNING: Machine registry is empty! No machines available for production.")
            
    except FileNotFoundError:
        logger.error(f"Factory config file not found at: {factory_config_path}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in factory config: {e}")
    except Exception as e:
        logger.error(f"Error loading machines from config: {e}", exc_info=True)


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


def handle_production_request(topic: str, payload: str):
    """Handle incoming production requests"""
    global workflow_registry

    try:
        # Parse JSON if it's a string (robust handling)
        if isinstance(payload, str):
            request = json.loads(payload)
        else:
            request = payload

        product_name = request.get("product_name")
        workflow_id = request.get("workflow_id")
        product_type = request.get("product_type")
        product_details = request.get("product_details", {})

        # Determine which workflow to use
        workflow = None
        if workflow_id:
            workflow = workflow_registry.get(workflow_id)
            if not workflow:
                logger.warning(f"Workflow ID '{workflow_id}' not found")
        elif product_type:
            workflow = workflow_registry.get_by_product_type(product_type)
            if not workflow:
                logger.warning(f"No workflow found for product type: {product_type}")
        
        # Fallback: try to find any workflow
        if not workflow:
            available_workflows = workflow_registry.list_all()
            if available_workflows:
                workflow = available_workflows[0]
                logger.info(f"Using first available workflow: {workflow.workflow_id}")
            else:
                available_ids = [w.workflow_id for w in workflow_registry.list_all()]
                logger.error(f"No workflows available. Requested: {workflow_id or product_type}. Available: {available_ids}")
                return

        # Create and queue order
        order = ProductionOrder(product_name, workflow, product_details)
        production_queue.put(order)

        logger.info(f"Queued order {order.order_id} with workflow '{workflow.workflow_name}'")

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in production request: {e}")
    except Exception as e:
        logger.error(f"Error handling production request: {e}", exc_info=True)


def handle_config_update(topic: str, payload: str):
    """Handle site-wide configuration updates (e.g. workflows, success rate)"""
    global orchestrator_instance, workflow_registry
    try:
        if isinstance(payload, str):
            config_data = json.loads(payload)
        else:
            config_data = payload

        logger.info(f"Received config update with {len(config_data)} root keys")
        
        # Load workflows from factory config if present
        workflows = config_data.get('workflows', [])
        if workflows:
            logger.info(f"Loading {len(workflows)} workflows from factory config")
            for workflow_data in workflows:
                try:
                    workflow = WorkflowDefinition.from_dict(workflow_data)
                    workflow_registry.register(workflow)
                    logger.info(f"✓ Loaded workflow: {workflow.workflow_name} ({workflow.workflow_id})")
                except Exception as e:
                    logger.error(f"Failed to load workflow {workflow_data.get('workflow_id', 'unknown')}: {e}")
        
        # Load machines from factory config if present
        machines = config_data.get('machines', [])
        if machines:
            logger.info(f"Processing {len(machines)} machines from factory config")
            for machine in machines:
                if machine.get('enabled', True):
                    machine_type = machine.get('machine_type')
                    machine_id = machine.get('machine_id')
                    if machine_type and machine_id:
                        register_machine(machine_type, machine_id)
        
        # Look for production configuration
        production_cfg = config_data.get("production_config", {})
        if "success_rate" in production_cfg:
            new_rate = float(production_cfg["success_rate"])
            logger.info(f"Updating production success rate to: {new_rate}")
            if orchestrator_instance:
                orchestrator_instance.production_success_rate = new_rate
        
    except Exception as e:
        logger.error(f"Error handling config update: {e}", exc_info=True)


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


def main():
    """Main service loop"""
    global running, workflow_registry, orchestrator_instance

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Starting Production Orchestrator V2 (Workflow-based)")

    # Initialize workflow registry and load from workflows directory
    workflows_dir = "/app/workflows"
    workflow_registry = WorkflowRegistry(workflows_dir=workflows_dir, load_defaults=True)
    
    logger.info(f"Loaded {len(workflow_registry.list_all())} workflows:")
    for workflow in workflow_registry.list_all():
        logger.info(f"  - {workflow.workflow_name} ({workflow.product_type}) - {len(workflow.steps)} steps")

    # Initialize MQTT client
    mqtt_client = MQTTClientWrapper(
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
    orchestrator_instance = orchestrator

    # Load machines from factory configuration
    factory_config_path = "/app/factory-config.json"
    if os.path.exists(factory_config_path):
        load_machines_from_config(factory_config_path)
    else:
        # Try alternative path
        alt_config_path = "/app/config/factory-config.json"
        if os.path.exists(alt_config_path):
            load_machines_from_config(alt_config_path)
        else:
            logger.warning(f"Factory config not found at {factory_config_path} or {alt_config_path}")
            logger.warning("Will rely on machine registration via MQTT")
    
    # Log current machine registry state
    logger.info(f"Current machine registry state: {dict(machine_registry)}")
    if not machine_registry:
        logger.error("⚠️  CRITICAL: No machines loaded! Production will fail until machines register.")

    # Machines can self-register via MQTT using the registration topic as a fallback.

    # Subscribe to topics
    request_topic = f"factory/{FACTORY_SITE_ID}/production/request"
    registration_topic = f"factory/{FACTORY_SITE_ID}/machine/+/+/register"
    config_topic = f"factory/{FACTORY_SITE_ID}/config"

    mqtt_client.subscribe(request_topic, handle_production_request)
    mqtt_client.subscribe(registration_topic, handle_machine_registration)
    mqtt_client.subscribe(config_topic, handle_config_update)

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
