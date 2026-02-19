"""
Workflow Engine - Flexible production workflow system
Allows defining different production processes with different machine sequences
"""
import json
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow"""
    step_id: str
    machine_type: str
    operation: str  # e.g., "cut", "sew", "iron", "print"
    required_inputs: List[str] = field(default_factory=list)
    optional_inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    parallel_group: Optional[int] = None  # Steps in same group can run in parallel
    timeout_seconds: int = 60
    retry_count: int = 0

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> 'WorkflowStep':
        return WorkflowStep(**data)


@dataclass
class WorkflowDefinition:
    """Defines a complete production workflow"""
    workflow_id: str
    workflow_name: str
    description: str
    product_type: str
    steps: List[WorkflowStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'workflow_id': self.workflow_id,
            'workflow_name': self.workflow_name,
            'description': self.description,
            'product_type': self.product_type,
            'steps': [step.to_dict() for step in self.steps],
            'metadata': self.metadata
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @staticmethod
    def from_dict(data: Dict) -> 'WorkflowDefinition':
        steps = [WorkflowStep.from_dict(s) for s in data.get('steps', [])]
        return WorkflowDefinition(
            workflow_id=data['workflow_id'],
            workflow_name=data['workflow_name'],
            description=data['description'],
            product_type=data['product_type'],
            steps=steps,
            metadata=data.get('metadata', {})
        )

    @staticmethod
    def from_json(json_str: str) -> 'WorkflowDefinition':
        return WorkflowDefinition.from_dict(json.loads(json_str))


class WorkflowRegistry:
    """Registry for managing workflow definitions"""

    def __init__(self, load_defaults: bool = True):
        self.workflows: Dict[str, WorkflowDefinition] = {}
        if load_defaults:
            self._load_default_workflows()

    def _load_default_workflows(self):
        """Load default workflow definitions"""
        # Standard T-Shirt workflow
        self.register(self._create_tshirt_workflow())

        # Hoodie workflow (includes additional steps)
        self.register(self._create_hoodie_workflow())

        # Simple workflow (cutting and printing only)
        self.register(self._create_simple_workflow())

        # Parallel workflow example
        self.register(self._create_parallel_workflow())

    def _create_tshirt_workflow(self) -> WorkflowDefinition:
        """Standard T-shirt production workflow"""
        return WorkflowDefinition(
            workflow_id="workflow-tshirt-standard",
            workflow_name="Standard T-Shirt Production",
            description="Complete t-shirt production: cutting, sewing, ironing, printing",
            product_type="tshirt",
            steps=[
                WorkflowStep(
                    step_id="step-1",
                    machine_type="cutting",
                    operation="cut_fabric",
                    required_inputs=["material", "cut_size"],
                    outputs=["cut_fabric"]
                ),
                WorkflowStep(
                    step_id="step-2",
                    machine_type="sewing",
                    operation="sew_pieces",
                    required_inputs=["cut_fabric", "stitch_type", "thread_color"],
                    outputs=["sewn_garment"]
                ),
                WorkflowStep(
                    step_id="step-3",
                    machine_type="ironing",
                    operation="iron_garment",
                    required_inputs=["sewn_garment", "iron_temperature_setpoint", "steam_level"],
                    outputs=["ironed_garment"]
                ),
                WorkflowStep(
                    step_id="step-4",
                    machine_type="printing",
                    operation="print_design",
                    required_inputs=["ironed_garment", "ink_type"],
                    optional_inputs=["design_name"],
                    outputs=["finished_product"]
                )
            ],
            metadata={"estimated_time_minutes": 20, "complexity": "standard"}
        )

    def _create_hoodie_workflow(self) -> WorkflowDefinition:
        """Hoodie production workflow with additional steps"""
        return WorkflowDefinition(
            workflow_id="workflow-hoodie-standard",
            workflow_name="Hoodie Production",
            description="Hoodie production with hood attachment",
            product_type="hoodie",
            steps=[
                WorkflowStep(
                    step_id="step-1",
                    machine_type="cutting",
                    operation="cut_body",
                    required_inputs=["material", "cut_size"],
                    outputs=["cut_body"]
                ),
                WorkflowStep(
                    step_id="step-2",
                    machine_type="cutting",
                    operation="cut_hood",
                    required_inputs=["material"],
                    outputs=["cut_hood"]
                ),
                WorkflowStep(
                    step_id="step-3",
                    machine_type="sewing",
                    operation="sew_body",
                    required_inputs=["cut_body", "stitch_type", "thread_color"],
                    outputs=["sewn_body"]
                ),
                WorkflowStep(
                    step_id="step-4",
                    machine_type="sewing",
                    operation="attach_hood",
                    required_inputs=["sewn_body", "cut_hood", "stitch_type", "thread_color"],
                    outputs=["hoodie_assembled"]
                ),
                WorkflowStep(
                    step_id="step-5",
                    machine_type="ironing",
                    operation="iron_hoodie",
                    required_inputs=["hoodie_assembled", "iron_temperature_setpoint", "steam_level"],
                    outputs=["ironed_hoodie"]
                ),
                WorkflowStep(
                    step_id="step-6",
                    machine_type="printing",
                    operation="print_design",
                    required_inputs=["ironed_hoodie", "ink_type"],
                    optional_inputs=["design_name"],
                    outputs=["finished_hoodie"]
                )
            ],
            metadata={"estimated_time_minutes": 35, "complexity": "complex"}
        )

    def _create_simple_workflow(self) -> WorkflowDefinition:
        """Simple workflow - cutting and printing only"""
        return WorkflowDefinition(
            workflow_id="workflow-simple-patch",
            workflow_name="Simple Patch Production",
            description="Quick production: cutting and printing only",
            product_type="patch",
            steps=[
                WorkflowStep(
                    step_id="step-1",
                    machine_type="cutting",
                    operation="cut_patch",
                    required_inputs=["material", "cut_size"],
                    outputs=["cut_patch"]
                ),
                WorkflowStep(
                    step_id="step-2",
                    machine_type="printing",
                    operation="print_patch",
                    required_inputs=["cut_patch", "ink_type"],
                    outputs=["finished_patch"]
                )
            ],
            metadata={"estimated_time_minutes": 10, "complexity": "simple"}
        )

    def _create_parallel_workflow(self) -> WorkflowDefinition:
        """Workflow with parallel processing steps"""
        return WorkflowDefinition(
            workflow_id="workflow-tshirt-parallel",
            workflow_name="T-Shirt with Parallel Processing",
            description="T-shirt with front and back processed in parallel",
            product_type="tshirt-parallel",
            steps=[
                # Cut front and back
                WorkflowStep(
                    step_id="step-1a",
                    machine_type="cutting",
                    operation="cut_front",
                    required_inputs=["material", "cut_size"],
                    outputs=["cut_front"],
                    parallel_group=1
                ),
                WorkflowStep(
                    step_id="step-1b",
                    machine_type="cutting",
                    operation="cut_back",
                    required_inputs=["material", "cut_size"],
                    outputs=["cut_back"],
                    parallel_group=1
                ),
                # Print front and back in parallel
                WorkflowStep(
                    step_id="step-2a",
                    machine_type="printing",
                    operation="print_front",
                    required_inputs=["cut_front", "ink_type"],
                    outputs=["printed_front"],
                    parallel_group=2
                ),
                WorkflowStep(
                    step_id="step-2b",
                    machine_type="printing",
                    operation="print_back",
                    required_inputs=["cut_back", "ink_type"],
                    outputs=["printed_back"],
                    parallel_group=2
                ),
                # Sew together (sequential)
                WorkflowStep(
                    step_id="step-3",
                    machine_type="sewing",
                    operation="sew_together",
                    required_inputs=["printed_front", "printed_back", "stitch_type", "thread_color"],
                    outputs=["assembled_tshirt"]
                ),
                # Final ironing
                WorkflowStep(
                    step_id="step-4",
                    machine_type="ironing",
                    operation="final_iron",
                    required_inputs=["assembled_tshirt", "iron_temperature_setpoint", "steam_level"],
                    outputs=["finished_tshirt"]
                )
            ],
            metadata={"estimated_time_minutes": 25, "complexity": "parallel", "supports_parallelization": True}
        )

    def register(self, workflow: WorkflowDefinition):
        """Register a workflow definition"""
        self.workflows[workflow.workflow_id] = workflow
        logger.info(f"Registered workflow: {workflow.workflow_name} ({workflow.workflow_id})")

    def get(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get a workflow by ID"""
        return self.workflows.get(workflow_id)

    def get_by_product_type(self, product_type: str) -> Optional[WorkflowDefinition]:
        """Get workflow by product type (returns first match)"""
        for workflow in self.workflows.values():
            if workflow.product_type == product_type:
                return workflow
        return None

    def list_all(self) -> List[WorkflowDefinition]:
        """List all registered workflows"""
        return list(self.workflows.values())

    def list_product_types(self) -> List[str]:
        """List all available product types"""
        return list(set(w.product_type for w in self.workflows.values()))

    def load_from_file(self, file_path: str):
        """Load workflow from JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                workflow = WorkflowDefinition.from_dict(data)
                self.register(workflow)
                logger.info(f"Loaded workflow from file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to load workflow from {file_path}: {e}")

    def save_to_file(self, workflow_id: str, file_path: str):
        """Save workflow to JSON file"""
        workflow = self.get(workflow_id)
        if not workflow:
            logger.error(f"Workflow not found: {workflow_id}")
            return

        try:
            with open(file_path, 'w') as f:
                f.write(workflow.to_json())
            logger.info(f"Saved workflow to file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save workflow to {file_path}: {e}")


class WorkflowValidator:
    """Validates workflow definitions and execution prerequisites"""

    @staticmethod
    def validate_definition(workflow: WorkflowDefinition) -> tuple[bool, List[str]]:
        """Validate workflow definition, returns (is_valid, errors)"""
        errors = []

        if not workflow.workflow_id:
            errors.append("Workflow ID is required")

        if not workflow.workflow_name:
            errors.append("Workflow name is required")

        if not workflow.steps:
            errors.append("Workflow must have at least one step")

        # Validate step IDs are unique
        step_ids = [s.step_id for s in workflow.steps]
        if len(step_ids) != len(set(step_ids)):
            errors.append("Step IDs must be unique")

        # Validate inputs/outputs consistency
        all_outputs = set()
        for step in workflow.steps:
            all_outputs.update(step.outputs)

        for step in workflow.steps:
            for required_input in step.required_inputs:
                # Check if required input comes from product details or previous steps
                if required_input not in all_outputs:
                    # It should be provided in product details
                    pass  # This is OK - will be validated at runtime

        return len(errors) == 0, errors

    @staticmethod
    def validate_inputs(step: WorkflowStep, available_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate that all required inputs are available"""
        errors = []

        for required_input in step.required_inputs:
            if required_input not in available_data:
                errors.append(f"Missing required input: {required_input}")

        return len(errors) == 0, errors

    @staticmethod
    def extract_process_data(step: WorkflowStep, product_details: Dict[str, Any]) -> Dict[str, Any]:
        """Extract process data for a step from product details"""
        process_data = {}

        # Extract required inputs
        for input_name in step.required_inputs:
            if input_name in product_details:
                process_data[input_name] = product_details[input_name]

        # Extract optional inputs
        for input_name in step.optional_inputs:
            if input_name in product_details:
                process_data[input_name] = product_details[input_name]

        return process_data
