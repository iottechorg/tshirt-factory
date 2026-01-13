import asyncio
from machine import Machine
from production import ProductionProcess
from mqtt_publisher import MQTTPublisher
import threading
import time
import logging

from util import *
from config import *

machines = [Machine(name) for name in MACHINE_NAMES]
machine_mqtt_publisher = MQTTPublisher(client_id="machine_simulator_machine")
production_mqtt_publisher = MQTTPublisher(client_id="machine_simulator_production")

# Move the production process creation inside the production manager
production_process = None


class MachineManager(threading.Thread):
    def __init__(self, all_machines, publisher):
        super().__init__(daemon=True)
        self.machines = all_machines
        self.publisher = publisher
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def run(self):
        self.publisher.connect()
        self.publisher.loop_start()
        machine_tasks = [self.loop.create_task(machine.run()) for machine in self.machines]
        self.loop.run_until_complete(asyncio.gather(*machine_tasks))
        self.loop.close()
        self.publisher.loop_stop()

    def publish_machine_data(self):
        while True:
            try:
                data = [json.loads(machine.to_json()) for machine in self.machines]
                self.publisher.publish(MQTT_TOPIC_MACHINE, json.dumps(data))
            except Exception as e:
                logging.error(f"Error generating or publishing message: {e}")
            time.sleep(MACHINE_DATA_PUBLISH_INTERVAL)

    def update_machine(self, machine_id, data):
        machine = get_machine_by_id(self.machines, machine_id)
        if not machine:
            logging.warning("Machine not found")
            return None
        if "failure_rate" in data:
            machine.failure_rate = float(data["failure_rate"])
        return machine

    def update_machine_sensor(self, machine_id, sensor_name, value):
        machine = get_machine_by_id(self.machines, machine_id)
        if not machine:
            logging.warning(f"Machine not found {machine_id}")
            return None
        if not machine.update_sensor_config(sensor_name, value):
            logging.warning(f"Sensor not found {sensor_name} for {machine_id}")
            return None
        return machine


class ProductionManager(threading.Thread):
    def __init__(self, publisher):
        super().__init__(daemon=True)
        self.publisher = publisher
        self.production_process = ProductionProcess(machines, publisher)

    def run(self):
        self.publisher.connect()
        self.publisher.loop_start()
        while True:
            self.production_process.process_production_request()
            time.sleep(PRODUCTION_LOOP_INTERVAL)

    def add_production_request(self, product_name, product_details=None):
        self.production_process.add_production_request(product_name, product_details)


machine_manager = MachineManager(machines, machine_mqtt_publisher)
production_manager = ProductionManager(production_mqtt_publisher)


def reload_machines_from_config(cfg: dict):
    """Adjust the in-memory machine instances to match the factory config.

    - Adds machines if the config contains more instances of a type
    - Stops and removes machines if the config has fewer
    """
    try:
        desired = {}
        for m in cfg.get('machines', []):
            t = m.get('machine_type')
            if not t:
                continue
            desired[t] = desired.get(t, 0) + 1

        # current counts by machine.name
        current = {}
        for m in machines:
            current[m.name] = current.get(m.name, 0) + 1

        # Add missing machines
        for mtype, count in desired.items():
            have = current.get(mtype, 0)
            if count > have:
                for _ in range(count - have):
                    newm = Machine(mtype)
                    machines.append(newm)
                    # If manager already running, schedule its loop task
                    try:
                        if machine_manager and machine_manager.loop and not machine_manager.loop.is_closed():
                            machine_manager.loop.call_soon_threadsafe(lambda nm=newm: machine_manager.loop.create_task(nm.run()))
                    except Exception:
                        pass

        # Remove extra machines
        for mtype, have in list(current.items()):
            want = desired.get(mtype, 0)
            if have > want:
                # remove (have - want) machines of this type
                to_remove = have - want
                removed = 0
                # iterate in reverse to remove newest first
                for i in range(len(machines) - 1, -1, -1):
                    if removed >= to_remove:
                        break
                    if machines[i].name == mtype:
                        try:
                            machines[i].stop()
                        except Exception:
                            pass
                        del machines[i]
                        removed += 1

        # update production manager's machines reference
        try:
            production_manager.production_process.machines = machines
        except Exception:
            pass

    except Exception as e:
        import logging
        logging.exception(f"Error reloading machines from config: {e}")


def config_watcher_thread(path: str = "factory_config_runtime.json", interval: int = 5):
    """Thread that polls a runtime config file and reloads machines when changed."""
    import time, json
    last_mtime = None
    while True:
        try:
            if os.path.exists(path):
                mtime = os.path.getmtime(path)
                if last_mtime is None or mtime > last_mtime:
                    with open(path, 'r') as f:
                        cfg = json.load(f)
                        reload_machines_from_config(cfg)
                    last_mtime = mtime
        except Exception:
            logging.exception("Error in config watcher")
        time.sleep(interval)


# Start config watcher in background so changes applied at runtime
try:
    import threading
    watcher = threading.Thread(target=config_watcher_thread, daemon=True)
    watcher.start()
except Exception:
    pass
