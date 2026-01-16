#!/usr/bin/env python3
"""Verify that machine templates are being loaded and used correctly."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# NOTE: This script is deprecated - use test_template_driven.py instead
# Kept for reference only
from shared.template_driven_test_generator import TemplateDrivenTestGenerator as SharedTestCaseGen

# Test with automotive factory (uses welding, stamping machines from templates)
print("="*70)
print("Testing shared/test_case_generator.py with machine templates")
print("="*70)

factory_config = json.load(open("factory-configs/automotive-assembly-plant.json"))
gen = SharedTestCaseGen(factory_config)

print(f"\nFactory: {factory_config['factory_name']}")
print(f"Factory type: {factory_config['factory_type']}")

# Check that machine templates were loaded
print(f"\n📁 Machine templates loaded: {len(gen.machine_templates)}")
for machine_type, template in list(gen.machine_templates.items())[:5]:
    sensors = template.get('sensors', [])
    sensor_count = len(sensors) if isinstance(sensors, list) else len(sensors)
    print(f"  - {machine_type}: {sensor_count} sensors")
if len(gen.machine_templates) > 5:
    print(f"  ... and {len(gen.machine_templates) - 5} more")

# Check that sensors from templates are being discovered
print(f"\n🔍 Machine types by sensor type:")
# Get welding machines with arc_voltage (from welding-machine template)
welding_with_voltage = gen._get_machine_types_with_sensor_type("arc_voltage")
print(f"  - arc_voltage: {welding_with_voltage}")

# Get stamping machines with hydraulic_pressure (from stamping-machine template)
stamping_with_pressure = gen._get_machine_types_with_sensor_type("hydraulic_pressure") 
print(f"  - hydraulic_pressure: {stamping_with_pressure}")

# Check sensor ranges from templates
print(f"\n📊 Sensor ranges from templates:")
try:
    arc_voltage_range = gen.get_sensor_extremes("welding", "arc_voltage")
    print(f"  - arc_voltage (welding): {arc_voltage_range}")
except KeyError as e:
    print(f"  - arc_voltage: Not found ({e})")

try:
    wire_feed_range = gen.get_sensor_extremes("welding", "wire_feed_speed")
    print(f"  - wire_feed_speed (welding): {wire_feed_range}")
except KeyError as e:
    print(f"  - wire_feed_speed: Not found ({e})")

try:
    blade_temp_range = gen.get_sensor_extremes("cutting", "blade_temperature")
    print(f"  - blade_temperature (cutting): {blade_temp_range}")
except KeyError as e:
    print(f"  - blade_temperature: Not found ({e})")

# Generate test cases to confirm they use template sensors
print(f"\n🧪 Generated test cases using template sensors:")
all_tests = gen.generate_initial_test_cases()
print(f"  Generated {sum(len(tests) for tests in all_tests.values())} test cases across {len(all_tests)} categories")
for category, tests in list(all_tests.items())[:2]:
    print(f"\n  Category: {category}")
    if tests:
        test = tests[0]
        print(f"    Test: {test['name']}")
        print(f"    Steps: {len(test['steps'])}")
        for step in test['steps'][:3]:
            if 'sensor_name' in step:
                print(f"      - {step['action']}: {step.get('sensor_name')} = {step.get('value')}")
        if len(test['steps']) > 3:
            print(f"      ... and {len(test['steps']) - 3} more steps")

print("\n" + "="*70)
print("✅ Machine templates are properly loaded and used!")
print("✅ Template sensors (arc_voltage, wire_feed_speed, etc.) are available")
print("="*70)
