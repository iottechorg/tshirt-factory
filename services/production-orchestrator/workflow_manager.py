#!/usr/bin/env python3
"""
Workflow Management Utility
Provides tools for managing production workflows, adjusting parameters, and monitoring performance
"""
import sys
import os
import json
import argparse
import time

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../shared'))

from mqtt_client import MQTTClient
from config import MQTT_BROKER, MQTT_PORT, FACTORY_SITE_ID


class WorkflowManager:
    """Utility for managing workflows via MQTT"""

    def __init__(self):
        self.mqtt_client = MQTTClient(
            client_id="workflow-manager-cli",
            broker=MQTT_BROKER,
            port=MQTT_PORT
        )
        self.response_received = False
        self.response_data = None

    def connect(self):
        """Connect to MQTT broker"""
        return self.mqtt_client.connect()

    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.mqtt_client.disconnect()

    def adjust_workflow_step(self, workflow_id: str, step_id: str, parameter: str, value: any):
        """Adjust a workflow step parameter"""
        topic = f"factory/{FACTORY_SITE_ID}/orchestrator/workflow/adjust"
        message = {
            "action": "adjust",
            "workflow_id": workflow_id,
            "step_id": step_id,
            "parameter": parameter,
            "value": value
        }

        self.mqtt_client.publish_json(topic, message)
        print(f"✓ Adjusted {workflow_id}/{step_id}: {parameter} = {value}")

    def query_performance(self):
        """Query machine performance metrics"""
        topic = f"factory/{FACTORY_SITE_ID}/orchestrator/performance/query"
        response_topic = f"factory/{FACTORY_SITE_ID}/orchestrator/performance/response"

        message = {
            "action": "query",
            "response_topic": response_topic
        }

        self.mqtt_client.publish_json(topic, message)
        print(f"✓ Performance query sent to orchestrator")

    def submit_production_order(self, product_name: str, workflow_id: str = None,
                               product_type: str = None, product_details: dict = None):
        """Submit a production order"""
        topic = f"factory/{FACTORY_SITE_ID}/production/request"
        message = {
            "product_name": product_name,
            "product_details": product_details or {}
        }

        if workflow_id:
            message["workflow_id"] = workflow_id
        elif product_type:
            message["product_type"] = product_type

        self.mqtt_client.publish_json(topic, message)
        print(f"✓ Production order submitted: {product_name}")
        if workflow_id:
            print(f"  Workflow: {workflow_id}")
        elif product_type:
            print(f"  Product Type: {product_type}")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Workflow Management Utility for Production Orchestrator"
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Adjust workflow command
    adjust_parser = subparsers.add_parser('adjust', help='Adjust workflow step parameters')
    adjust_parser.add_argument('--workflow', required=True, help='Workflow ID')
    adjust_parser.add_argument('--step', required=True, help='Step ID')
    adjust_parser.add_argument('--param', required=True,
                              choices=['timeout_seconds', 'retry_count'],
                              help='Parameter to adjust')
    adjust_parser.add_argument('--value', required=True, type=int, help='New value')

    # Performance query command
    perf_parser = subparsers.add_parser('performance', help='Query machine performance')

    # Submit order command
    order_parser = subparsers.add_parser('order', help='Submit production order')
    order_parser.add_argument('--name', required=True, help='Product name')
    order_parser.add_argument('--workflow', help='Workflow ID')
    order_parser.add_argument('--type', help='Product type')
    order_parser.add_argument('--details', help='Product details (JSON)')

    # List workflows command
    list_parser = subparsers.add_parser('list', help='List available workflows')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Create manager and connect
    manager = WorkflowManager()

    if not manager.connect():
        print("✗ Failed to connect to MQTT broker")
        return

    try:
        if args.command == 'adjust':
            manager.adjust_workflow_step(
                args.workflow,
                args.step,
                args.param,
                args.value
            )

        elif args.command == 'performance':
            manager.query_performance()

        elif args.command == 'order':
            details = {}
            if args.details:
                try:
                    details = json.loads(args.details)
                except json.JSONDecodeError:
                    print("✗ Invalid JSON in --details")
                    return

            manager.submit_production_order(
                args.name,
                workflow_id=args.workflow,
                product_type=args.type,
                product_details=details
            )

        elif args.command == 'list':
            # List workflows from directory
            workflows_dir = os.path.join(os.path.dirname(__file__), "../../workflows")
            if os.path.exists(workflows_dir):
                print("\nAvailable Workflows:")
                print("-" * 80)

                import glob
                workflow_files = glob.glob(os.path.join(workflows_dir, "*.json"))

                for file_path in sorted(workflow_files):
                    try:
                        with open(file_path, 'r') as f:
                            workflow = json.load(f)
                            print(f"\n  ID: {workflow['workflow_id']}")
                            print(f"  Name: {workflow['workflow_name']}")
                            print(f"  Type: {workflow['product_type']}")
                            print(f"  Steps: {len(workflow['steps'])}")

                            # Show steps
                            for i, step in enumerate(workflow['steps'], 1):
                                print(f"    {i}. {step['operation']} ({step['machine_type']}) - "
                                      f"timeout: {step['timeout_seconds']}s, "
                                      f"retries: {step['retry_count']}")

                    except Exception as e:
                        print(f"  Error loading {os.path.basename(file_path)}: {e}")

                print("\n" + "-" * 80)
            else:
                print(f"✗ Workflows directory not found: {workflows_dir}")

        # Brief pause to allow message delivery
        time.sleep(0.5)

    finally:
        manager.disconnect()


if __name__ == "__main__":
    main()
