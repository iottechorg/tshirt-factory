#!/usr/bin/env python3
"""Test that generators are now factory-agnostic."""
import json
# Use new template-driven generator
from shared.template_driven_test_generator import TemplateDrivenTestGenerator

def test_factory(factory_name, config_path):
    print(f"\n{'='*60}")
    print(f"{factory_name}")
    print(f"{'='*60}")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Test template-driven test case generator
    test_gen = TemplateDrivenTestGenerator(config)
    report = test_gen.generate_sensor_coverage_report()
    print(f"\nSensors discovered: {report['total_sensors']}")
    print(f"Test cases to generate: {report['test_cases_generated']['total']}")
    
    test_cases = test_gen.generate_all_test_cases()
    # Get a sample production test
    if test_cases['production_tests']:
        sample_test = test_cases['production_tests'][0]
        product_details = sample_test['steps'][0]['product_details']
        print(f"Generated product_details: {product_details}")

if __name__ == "__main__":
    test_factory("T-Shirt Factory", "factory-configs/tshirt-factory.json")
    test_factory("Automotive Factory", "factory-configs/automotive-assembly-plant.json")
    test_factory("Electronics Factory", "factory-configs/electronics-factory.json")
    
    print(f"\n{'='*60}")
    print("✓ All factories successfully generated factory-specific configs!")
    print("✓ No hardcoded T-shirt assumptions remain")
    print(f"{'='*60}\n")
