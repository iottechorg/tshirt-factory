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
            import time
            client_id = f"factory_ui_state_{self.factory_site_id}_{int(time.time())}"
            self.mqtt_client = mqtt.Client(client_id=client_id)
            self.mqtt_client.on_connect = self._on_connect
            self.mqtt_client.on_message = self._on_message
            self.mqtt_client.on_disconnect = self._on_disconnect
            
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
            # Support both legacy 'machines' topic layout and canonical 'machine/{type}/{id}' layout
            try:
                client.subscribe(f"factory/{self.factory_site_id}/machines/+/+")
                client.subscribe(f"factory/{self.factory_site_id}/machine/#")
                client.subscribe(f"factory/{self.factory_site_id}/production/#")
                logger.info(f"Subscribed to factory/{self.factory_site_id}/machines/+/+, machine/# and /production/#")
            except Exception as e:
                logger.error(f"Error subscribing to topics: {e}")
        else:
            logger.error(f"MQTT connection failed with rc={rc}")
            self.is_connected = False
    
    def _on_disconnect(self, client, userdata, rc):
        """MQTT on_disconnect callback."""
        self.is_connected = False
        if rc != 0:
            logger.info(f"MQTT state manager disconnected unexpectedly with code: {rc}")
            # Attempt to reconnect
            logger.info("Attempting to reconnect MQTT state manager...")
            try:
                self.mqtt_client.reconnect()
            except Exception as e:
                logger.error(f"MQTT state manager reconnection failed: {e}")
    
    def _on_message(self, client, userdata, msg):
        """MQTT on_message callback."""
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8")
            # Per-machine topics: factory/{factory_id}/machines/{machine_id}/{data_type}
            if f"factory/{self.factory_site_id}/machines/" in topic:
                self._handle_machine_topic(topic, payload)
            elif f"factory/{self.factory_site_id}/production/" in topic:
                self._handle_production_topic(topic, payload)
            else:
                logger.debug(f"Unhandled MQTT topic: {topic}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def _handle_production_topic(self, topic: str, payload: str):
        """Handle production related topics (status, results)."""
        try:
            data = json.loads(payload)
            # Handle both status and result
            with self.state_lock:
                if self.factory_site_id not in self.factory_states:
                    self.factory_states[self.factory_site_id] = {"machines": {}, "production_status": None}
                
                # Check if it's a result or just status
                if topic.endswith("/result"):
                    # For results, we might want to keep a history or just the latest
                    self.factory_states[self.factory_site_id]["production_status"] = data
                    logger.info(f"Received production RESULT for order {data.get('order_id')}: {data.get('status')}")
                elif topic.endswith("/status"):
                    # Status updates
                    self.factory_states[self.factory_site_id]["production_status"] = data
                    logger.debug(f"Received production status update for order {data.get('order_id')}: {data.get('status')}")
        except Exception as e:
            logger.error(f"Error handling production topic {topic}: {e}")

    def _handle_machine_topic(self, topic: str, payload: str):
        """Handle per-machine topics and aggregate into factory state."""
        try:
            parts = topic.split('/')
            # Handle both formats:
            # - legacy: factory/{site}/machines/{machine_id}/{data_type}
            # - canonical: factory/{site}/machine/{machine_type}/{machine_id}/{data_type}
            if len(parts) < 5:
                logger.warning(f"Unexpected machine topic format: {topic}")
                return

            if parts[2] == 'machines':
                # legacy layout
                machine_type = None
                machine_id = parts[3]
                data_type = parts[4]
            elif parts[2] == 'machine':
                # canonical layout
                if len(parts) < 6:
                    logger.warning(f"Unexpected canonical machine topic format: {topic}")
                    return
                machine_type = parts[3]
                machine_id = parts[4]
                data_type = parts[5]
            else:
                logger.warning(f"Unhandled machine topic prefix: {parts[2]} in {topic}")
                return
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
                    inferred_type = machine_type or machine_id.rsplit('-', 1)[0]
                    machines_map[machine_id] = {
                        "id": machine_id,
                        "machine_id": machine_id,
                        "machine_type": inferred_type,
                        "instance_name": data.get("instance_name") or machine_id,
                        "name": data.get("instance_name") or machine_id,
                        "sensor_data": {},
                        "process_data": {},
                        "runtime_state": "unknown",
                    }

                entry = machines_map[machine_id]
                # ensure machine_type is present and updated from canonical topics
                if machine_type:
                    entry['machine_type'] = machine_type
                if data_type == "telemetry":
                    # telemetry payload expected to contain sensor_data
                    if isinstance(data, dict):
                        entry.setdefault("sensor_data", {}).update(data.get("sensor_data", {}))
                        entry["runtime_state"] = data.get("runtime_state", entry.get("runtime_state"))
                elif data_type == "status":
                    # status payload may contain runtime_state, process_data, failure_rate, and other metrics
                    if isinstance(data, dict):
                        entry.setdefault("sensor_data", {}).update(data.get("sensor_data", {}))
                        entry.setdefault("process_data", {}).update(data.get("process_data", {}))
                        entry["runtime_state"] = data.get("runtime_state", entry.get("runtime_state"))
                        # Update failure_rate and other status metrics
                        if "failure_rate" in data:
                            entry["failure_rate"] = data["failure_rate"]
                        if "total_operations" in data:
                            entry["total_operations"] = data["total_operations"]
                        if "failed_operations" in data:
                            entry["failed_operations"] = data["failed_operations"]
                        if "uptime_seconds" in data:
                            entry["uptime_seconds"] = data["uptime_seconds"]
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
                return list(self.factory_states[self.factory_site_id].get("machines", {}).values())
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
