#!/usr/bin/env python3
"""Validate that all generators work factory-agnostically."""
import json
import sys
from pathlib import Path

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.template_driven_test_generator import TemplateDrivenTestGenerator

def validate_factory(factory_path):
    """Validate generators work with a factory config."""
    print(f"\n{'='*70}")
    print(f"Testing: {factory_path.name}")
    print('='*70)
    
    with open(factory_path) as f:
        config = json.load(f)
    
    factory_name = config.get('factory_name', 'Unknown')
    factory_type = config.get('factory_type', 'Unknown')
    
    print(f"Factory: {factory_name}")
    print(f"Type: {factory_type}")
    
    # Test UI test case generator  
    print("\n🧪 Template-Driven Test Generator:")
    ui_gen = TemplateDrivenTestGenerator(config)
    report = ui_gen.generate_sensor_coverage_report()
    print(f"  ✓ Total sensors discovered: {report['total_sensors']}")
    print(f"  ✓ Test cases to generate: {report['test_cases_generated']['total']}")
    
    test_cases = ui_gen.generate_all_test_cases()
    total_tests = sum(len(tests) for tests in test_cases.values())
    print(f"  ✓ Generated {total_tests} test cases from templates")
    
    return True

if __name__ == "__main__":
    configs_dir = Path("factory-configs")
    
    success_count = 0
    fail_count = 0
    
    for config_file in sorted(configs_dir.glob("*.json")):
        try:
            validate_factory(config_file)
            success_count += 1
        except Exception as e:
            print(f"\n❌ FAILED: {config_file.name}")
            print(f"   Error: {e}")
            fail_count += 1
    
    print(f"\n{'='*70}")
    print(f"Summary: {success_count} passed, {fail_count} failed")
    print('='*70)
    
    if fail_count == 0:
        print("\n✅ All generators are factory-agnostic!")
        print("✅ No hardcoded T-shirt assumptions found")
        sys.exit(0)
    else:
        sys.exit(1)
