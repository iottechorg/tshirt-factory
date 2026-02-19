"""
Workflow Engine - Flexible production workflow system
Allows defining different production processes with different machine sequences
"""
import json
import logging
import os
from pathlib import Path
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

    def __init__(self, workflows_dir: Optional[str] = None, load_defaults: bool = True):
        self.workflows: Dict[str, WorkflowDefinition] = {}
        
        # Load from directory if provided
        if workflows_dir and os.path.isdir(workflows_dir):
            self.load_from_directory(workflows_dir)
        elif load_defaults:
            logger.warning("No workflows directory provided and load_defaults=True. Registry will be empty unless workflows are loaded via load_from_file().")

    def load_from_directory(self, workflows_dir: str):
        """Load all workflow JSON files from a directory"""
        workflows_path = Path(workflows_dir)
        if not workflows_path.is_dir():
            logger.warning(f"Workflows directory not found: {workflows_dir}")
            return
        
        json_files = sorted(workflows_path.glob('*.json'))
        if not json_files:
            logger.warning(f"No workflow JSON files found in {workflows_dir}")
            return
        
        for json_file in json_files:
            try:
                self.load_from_file(str(json_file))
            except Exception as e:
                logger.error(f"Failed to load workflow from {json_file}: {e}")
        
        if self.workflows:
            logger.info(f"Loaded {len(self.workflows)} workflows from {workflows_dir}")



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
