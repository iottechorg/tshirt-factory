# client.py
import requests
import json
import time
import random

API_BASE_URL = "http://localhost:5001"
TEST_CASE_FILE = "./static/test_cases.json"


def get_machines():
    url = f"{API_BASE_URL}/machines"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def update_machine(machine_id, data):
    url = f"{API_BASE_URL}/machines/{machine_id}"
    response = requests.put(url, json=data)
    response.raise_for_status()
    return response.json()


def update_machine_sensor(machine_id, sensor_name, value):
    url = f"{API_BASE_URL}/machines/sensor/{machine_id}/{sensor_name}"
    response = requests.put(url, json={'value': value})
    response.raise_for_status()
    return response.json()


def create_production_request(product_name, product_details=None):
    url = f"{API_BASE_URL}/production"
    payload = {"product_name": product_name, "product_details": product_details}
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()


def update_production_config(success_rate):
    url = f"{API_BASE_URL}/production/config"
    payload = {"success_rate": success_rate}
    response = requests.put(url, json=payload)
    response.raise_for_status()
    return response.json()


def execute_test_case(test_case):
    print(f"\nExecuting test case: {test_case['name']}")
    for step in test_case["steps"]:
        try:
            if step["action"] == "update_sensor":
                machines = get_machines()
                machine = next((m for m in machines if m["name"] == step["machine_name"]), None)
                if machine:
                    updated_machine = update_machine_sensor(machine["id"], step["sensor_name"], step["value"])
                    print(f"Updated sensor: {json.dumps(updated_machine, indent=2)}")
                else:
                    print(f"Machine {step['machine_name']} not found")
            elif step["action"] == "update_failure_rate":
                machines = get_machines()
                machine = next((m for m in machines if m["name"] == step["machine_name"]), None)
                if machine:
                    updated_machine = update_machine(machine["id"], {"failure_rate": step["failure_rate"]})
                    print(f"Updated failure rate: {json.dumps(updated_machine, indent=2)}")
            elif step["action"] == "production_request":
                result = create_production_request(step["product_name"], step["details"])
                print(f"Production request created: {result}")
            elif step["action"] == "update_production_success_rate":
                result = update_production_config(step["success_rate"])
                print(f"Production config updated: {result}")
        except requests.exceptions.RequestException as e:
            print(f"Error during API request: {e}")
        except ValueError as ve:
            print(f"Invalid input: {ve}")
        time.sleep(1)


def load_test_cases():
    try:
        with open(TEST_CASE_FILE, 'r') as f:
            return json.load(f).get("test_cases", [])
    except FileNotFoundError:
        print(f"Test case file '{TEST_CASE_FILE}' not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error decoding JSON in '{TEST_CASE_FILE}'.")
        return []


def generate_random_test_case(num_steps=5):
    machines = get_machines()
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
                print("No machine info found")
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

        elif action_type == "update_failure_rate":
            if not machines:
                print("No machine info found")
                continue
            machine = random.choice(machines)
            if not machine:
                continue
            failure_rate = round(random.uniform(0, 1), 2)
            test_case["steps"].append({
                "action": "update_failure_rate",
                "machine_name": machine["name"],
                "failure_rate": failure_rate
            })

        elif action_type == "production_request":
            product_details = {
                "material": random.choice(["Cotton", "Denim", "Polyester"]),
                "cut_size": random.choice(["Small", "Medium", "Large"]),
                "stitch_type": random.choice(["Straight", "Zigzag", "Chain"]),
                "thread_color": random.choice(["Red", "Blue", "Green", "Black", "White"]),
                "iron_temperature_setpoint": random.randint(100, 150),
                "steam_level": random.choice(["Low", "Medium", "High"]),
                "design_name": random.choice(["Logo1", "Logo2", "None"]),
                "ink_type": random.choice(["Water-based", "Oil-based", "None"])
            }
            test_case["steps"].append({
                "action": "production_request",
                "product_name": "T-Shirt",
                "details": product_details
            })
        elif action_type == "update_production_success_rate":
            success_rate = round(random.uniform(0, 1), 2)
            test_case["steps"].append({
                "action": "update_production_success_rate",
                "success_rate": success_rate
            })
    return test_case


def main():
    print("Welcome to the Factory Simulator Client!")
    test_cases = load_test_cases()
    while True:
        print("\nOptions:")
        print("1. Get Machines Status")
        print("2. Run Test Case")
        print("3. Run All Test Cases")
        print("4. Generate and Run Random Test Case")
        print("5. Exit")
        choice = input("Enter your choice: ")

        try:
            if choice == "1":
                machines = get_machines()
                print(json.dumps(machines, indent=2))
            elif choice == "2":
                if not test_cases:
                    print("No test cases loaded. Please check 'test_cases.json'.")
                    continue
                print("\nAvailable Test Cases:")
                for i, case in enumerate(test_cases):
                    print(f"{i + 1}. {case['name']}: {case['description']}")
                case_number = int(input("Enter the number of test case to run: "))
                if 1 <= case_number <= len(test_cases):
                    execute_test_case(test_cases[case_number - 1])
                else:
                    print("Invalid test case number.")
            elif choice == "3":
                if not test_cases:
                    print("No test cases loaded. Please check 'test_cases.json'.")
                    continue
                for case in test_cases:
                    execute_test_case(case)
            elif choice == "4":
                test_case = generate_random_test_case()
                execute_test_case(test_case)
            elif choice == "5":
                break
            else:
                print("Invalid choice. Please try again")
        except requests.exceptions.RequestException as e:
            print(f"Error during API request: {e}")
        except ValueError as ve:
            print(f"Invalid input: {ve}")
        except Exception as ex:
            print(f"An unexpected error occurred: {ex}")


if __name__ == "__main__":
    main()
