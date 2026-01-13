"""
Factory State Manager

Maintains in-memory state of connected factories received via MQTT.
Provides interface for REST endpoints to query factory status and send commands.

Architecture:
- Subscribes to factory/{site_id}/machines/status to receive machine state
- Subscribes to factory/{site_id}/production/status to receive production updates
- Provides query methods for REST endpoints to get current machine/production status
- When REST endpoint receives a command, it publishes to factory/{site_id}/<cmd_topic>
"""

import json
import logging
import threading
from typing import Dict, List, Optional, Any
from uuid import uuid4
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class FactoryStateManager:
    """Manages state of one or more factories via MQTT subscriptions."""

    def __init__(self, mqtt_broker: str, mqtt_port: int, factory_site_id: str):
        """
        Initialize factory state manager.
        
        Args:
            mqtt_broker: MQTT broker hostname/IP
            mqtt_port: MQTT broker port
            factory_site_id: Factory site identifier (e.g., "tshirt-factory-001")
        """
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.factory_site_id = factory_site_id
        
        # In-memory state: {factory_site_id -> {machines: [...], production_status: {...}}}
        self.factory_states = {}
        self.state_lock = threading.RLock()
        
        # MQTT client for subscriptions (receiving)
        self.mqtt_client = None
        self.is_connected = False
        
    def connect(self):
        """Connect to MQTT broker and start subscriptions."""
        try:
            self.mqtt_client = mqtt.Client(client_id=f"factory_ui_state_{self.factory_site_id}")
            self.mqtt_client.on_connect = self._on_connect
            self.mqtt_client.on_message = self._on_message
            
            logger.info(f"Connecting to MQTT broker {self.mqtt_broker}:{self.mqtt_port}")
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            logger.info("MQTT state manager loop started")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise
    
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT on_connect callback."""
        if rc == 0:
            logger.info("MQTT state manager connected to broker")
            self.is_connected = True
            # Subscribe to per-machine topics (telemetry/status) using wildcard
            client.subscribe(f"factory/{self.factory_site_id}/machines/+/+")
            # Subscribe to production-level status (aggregated by orchestrator)
            client.subscribe(f"factory/{self.factory_site_id}/production/status")
            logger.info(f"Subscribed to factory/{self.factory_site_id}/machines/+/+ and /production/status")
        else:
            logger.error(f"MQTT connection failed with rc={rc}")
            self.is_connected = False
    
    def _on_message(self, client, userdata, msg):
        """MQTT on_message callback."""
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8")
            # Per-machine topics: factory/{factory_id}/machines/{machine_id}/{data_type}
            if f"factory/{self.factory_site_id}/machines/" in topic:
                self._handle_machine_topic(topic, payload)
            elif f"factory/{self.factory_site_id}/production/status" in topic:
                self._handle_production_status(payload)
            else:
                logger.debug(f"Unhandled MQTT topic: {topic}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def _handle_machine_topic(self, topic: str, payload: str):
        """Handle per-machine topics and aggregate into factory state."""
        try:
            parts = topic.split('/')
            # expected: ["factory", factory_id, "machines", machine_id, data_type]
            if len(parts) < 5:
                logger.warning(f"Unexpected machine topic format: {topic}")
                return

            machine_id = parts[3]
            data_type = parts[4]  # 'status' or 'telemetry' or other
            try:
                data = json.loads(payload)
            except Exception:
                logger.error(f"Invalid JSON payload for topic {topic}")
                return

            with self.state_lock:
                if self.factory_site_id not in self.factory_states:
                    self.factory_states[self.factory_site_id] = {"machines": {}, "production_status": None}

                machines_map = self.factory_states[self.factory_site_id]["machines"]
                if machine_id not in machines_map:
                    # initialize machine entry
                    machines_map[machine_id] = {
                        "id": machine_id,
                        "machine_id": machine_id,
                        "machine_type": machine_id.rsplit('-', 1)[0],
                        "instance_name": data.get("instance_name") or machine_id,
                        "sensor_data": {},
                        "process_data": {},
                        "runtime_state": "unknown",
                    }

                entry = machines_map[machine_id]
                if data_type == "telemetry":
                    # telemetry payload expected to contain sensor_data
                    if isinstance(data, dict):
                        entry.setdefault("sensor_data", {}).update(data.get("sensor_data", {}))
                        entry["runtime_state"] = data.get("runtime_state", entry.get("runtime_state"))
                elif data_type == "status":
                    # status payload may contain runtime_state, process_data, etc.
                    if isinstance(data, dict):
                        entry.setdefault("sensor_data", {}).update(data.get("sensor_data", {}))
                        entry.setdefault("process_data", {}).update(data.get("process_data", {}))
                        entry["runtime_state"] = data.get("runtime_state", entry.get("runtime_state"))
                else:
                    # other data types (operation/result etc.) store under last_<type>
                    entry[f"last_{data_type}"] = data

                logger.debug(f"Updated machine {machine_id} ({data_type}) in cache")

        except Exception as e:
            logger.error(f"Error handling machine topic {topic}: {e}")
    
    def _handle_machines_status(self, payload: str):
        """Deprecated: aggregate machines status handler kept for backward compatibility."""
        try:
            data = json.loads(payload)
            with self.state_lock:
                if self.factory_site_id not in self.factory_states:
                    self.factory_states[self.factory_site_id] = {"machines": {}, "production_status": None}
                # convert list to map by id
                machines_map = {m.get("id") or m.get("machine_id"): m for m in data if isinstance(m, dict)}
                self.factory_states[self.factory_site_id]["machines"].update(machines_map)
            logger.debug(f"Updated machines state (aggregate): {len(machines_map)} machines")
        except Exception as e:
            logger.error(f"Error handling machines status: {e}")
    
    def _handle_production_status(self, payload: str):
        """Handle incoming production status message."""
        try:
            data = json.loads(payload)
            with self.state_lock:
                if self.factory_site_id not in self.factory_states:
                    self.factory_states[self.factory_site_id] = {"machines": [], "production_status": None}
                self.factory_states[self.factory_site_id]["production_status"] = data
            logger.debug(f"Updated production status: {data.get('status', 'unknown')}")
        except Exception as e:
            logger.error(f"Error handling production status: {e}")
    
    def get_machines(self) -> List[Dict[str, Any]]:
        """Get current machines state for factory."""
        with self.state_lock:
            if self.factory_site_id in self.factory_states:
                return self.factory_states[self.factory_site_id].get("machines", [])
        return []
    
    def get_machine(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """Get specific machine by ID."""
        machines = self.get_machines()
        for machine in machines:
            if machine.get("id") == machine_id or machine.get("machine_id") == machine_id:
                return machine
        return None
    
    def get_production_status(self) -> Optional[Dict[str, Any]]:
        """Get current production status."""
        with self.state_lock:
            if self.factory_site_id in self.factory_states:
                return self.factory_states[self.factory_site_id].get("production_status")
        return None
    
    def update_sensor_cache(self, machine_id: str, sensor_name: str, value: float) -> Optional[Dict[str, Any]]:
        """
        Update sensor value in local cache (visual feedback).
        Also update the machine's process_data if applicable.
        
        Returns:
            Updated machine object or None if not found.
        """
        with self.state_lock:
            machine = self.get_machine(machine_id)
            if not machine:
                logger.warning(f"Machine {machine_id} not found in state")
                return None
            
            # Update sensor_data
            if "sensor_data" not in machine:
                machine["sensor_data"] = {}
            machine["sensor_data"][sensor_name] = float(value)
            logger.debug(f"Updated cache: machine {machine_id}, sensor {sensor_name} = {value}")
            return machine
    
    def stop(self):
        """Stop MQTT client."""
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            logger.info("MQTT state manager stopped")
