# util.py
import random
from flask import jsonify
import logging
import re
import socket
import json

def get_machine_by_id(machines, machine_id):
    for machine in machines:
        if machine.id == machine_id:
            return machine
    return None


def generate_random_product_details():
    materials = ["Cotton", "Denim", "Polyester"]
    sizes = ["Small", "Medium", "Large", "X-Large"]
    stitch_types = ["Straight", "Zigzag", "Overlock"]
    thread_colors = ["Red", "Blue", "Green", "Black", "White"]
    iron_temps = [100, 110, 120, 130, 140, 150]
    steam_levels = ["Low", "Medium", "High"]
    design_names = ["Logo1", "Logo2", "Pattern1", "None"]
    ink_types = ["Water-based", "Oil-based", "None"]
    return {
        "material": random.choice(materials),
        "cut_size": random.choice(sizes),
        "stitch_type": random.choice(stitch_types),
        "thread_color": random.choice(thread_colors),
        "iron_temperature_setpoint": random.choice(iron_temps),
        "steam_level": random.choice(steam_levels),
        "design_name": random.choice(design_names),
        "ink_type": random.choice(ink_types)
    }


def generate_random_test_case(machines, num_steps=5):
    test_case = {
        "name": f"random_test_{random.randint(1000, 9999)}",
        "description": "Randomly generated test case.",
        "steps": []
    }
    for _ in range(num_steps):
        action_type = random.choice(
            ["update_sensor", "update_failure_rate", "production_request", "update_production_success_rate"])

        if action_type == "update_sensor":
            if not machines:
                logging.warning("No machine info found")
                continue
            machine = random.choice(machines)
            if not machine:
                continue
            sensor_names = list(machine.get("sensor_data", {}).keys())
            if not sensor_names:
                continue
            sensor_name = random.choice(sensor_names)
            value = round(random.uniform(0.1, 150), 2)
            test_case["steps"].append({
                "action": "update_sensor",
                "machine_name": machine["name"],
                "sensor_name": sensor_name,
                "value": value
            })
        elif action_type == "production_request":
            product_details = generate_random_product_details()
            test_case["steps"].append({
                "action": "production_request",
                "product_name": "T-Shirt",
                "details": product_details
            })
        elif action_type == "update_production_success_rate":
            success_rate = round(random.uniform(0.5, 1), 2)
            test_case["steps"].append({
                "action": "update_production_success_rate",
                "success_rate": success_rate
            })
    return test_case


def create_response(data, status_code=200):
    response = jsonify(data)
    response.status_code = status_code
    return response


def resolve_address(address):
    """
    Resolves the given address to 'localhost' if it's a Docker container name,
    or returns the original address if it's a server address or IP.
    """
    # Docker container names don't have a domain or look like IPs
    container_name_pattern = r"^[a-zA-Z0-9_.-]+$"
    ip_pattern = r"^\d{1,3}(\.\d{1,3}){3}$"  # Matches IPv4 addresses

    if re.match(container_name_pattern, address):
        if not re.match(ip_pattern, address) and "." not in address:
            # Likely a container name
            try:
                # Check if the name resolves (Docker container names often do)
                socket.gethostbyname(address)
                return "localhost"
            except socket.gaierror:
                # If resolution fails, treat it as non-container
                pass
    return address
