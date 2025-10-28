"""
Enhanced MQTT client with subscription support and better error handling
"""
import paho.mqtt.client as mqtt
import logging
import json
import time
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class MQTTClient:
    """Enhanced MQTT client for both publishing and subscribing"""

    def __init__(self, client_id: str, broker: str, port: int = 1883,
                 keepalive: int = 60, enable_logs: bool = True):
        self.client_id = client_id
        self.broker = broker
        self.port = port
        self.keepalive = keepalive
        self.enable_logs = enable_logs
        self.is_connected = False
        self.subscriptions = {}  # topic -> callback mapping

        # Create MQTT client
        self.client = mqtt.Client(client_id)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connection is established"""
        if rc == 0:
            self.is_connected = True
            if self.enable_logs:
                logger.info(f"[{self.client_id}] Connected to MQTT Broker at {self.broker}:{self.port}")

            # Re-subscribe to all topics after reconnection
            for topic in self.subscriptions.keys():
                self.client.subscribe(topic)
                if self.enable_logs:
                    logger.info(f"[{self.client_id}] Re-subscribed to topic: {topic}")
        else:
            logger.error(f"[{self.client_id}] Failed to connect, return code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected"""
        self.is_connected = False
        if rc != 0:
            logger.warning(f"[{self.client_id}] Disconnected unexpectedly with code: {rc}")
        else:
            if self.enable_logs:
                logger.info(f"[{self.client_id}] Disconnected from MQTT Broker")

    def _on_message(self, client, userdata, msg):
        """Callback when message is received"""
        topic = msg.topic
        payload = msg.payload.decode('utf-8')

        if self.enable_logs:
            logger.debug(f"[{self.client_id}] Received message on topic '{topic}': {payload[:100]}")

        # Call registered callback for this topic
        if topic in self.subscriptions:
            try:
                self.subscriptions[topic](topic, payload)
            except Exception as e:
                logger.error(f"[{self.client_id}] Error in message callback for topic '{topic}': {e}")

    def connect(self, retry_count: int = 5, retry_delay: int = 5):
        """Connect to MQTT broker with retry logic"""
        for attempt in range(retry_count):
            try:
                logger.info(f"[{self.client_id}] Attempting to connect to {self.broker}:{self.port} (attempt {attempt + 1}/{retry_count})")
                self.client.connect(self.broker, self.port, self.keepalive)
                return True
            except Exception as e:
                logger.error(f"[{self.client_id}] Connection attempt {attempt + 1} failed: {e}")
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)

        logger.error(f"[{self.client_id}] Failed to connect after {retry_count} attempts")
        return False

    def disconnect(self):
        """Disconnect from MQTT broker"""
        try:
            self.client.disconnect()
            if self.enable_logs:
                logger.info(f"[{self.client_id}] Disconnected from MQTT broker")
        except Exception as e:
            logger.error(f"[{self.client_id}] Error disconnecting: {e}")

    def subscribe(self, topic: str, callback: Callable[[str, str], None]):
        """Subscribe to a topic with a callback function"""
        self.subscriptions[topic] = callback
        if self.is_connected:
            self.client.subscribe(topic)
            if self.enable_logs:
                logger.info(f"[{self.client_id}] Subscribed to topic: {topic}")
        else:
            logger.warning(f"[{self.client_id}] Not connected, subscription to '{topic}' will be applied on connect")

    def unsubscribe(self, topic: str):
        """Unsubscribe from a topic"""
        if topic in self.subscriptions:
            del self.subscriptions[topic]
            if self.is_connected:
                self.client.unsubscribe(topic)
                if self.enable_logs:
                    logger.info(f"[{self.client_id}] Unsubscribed from topic: {topic}")

    def publish(self, topic: str, message: str, qos: int = 0, retain: bool = False):
        """Publish a message to a topic"""
        if self.is_connected:
            try:
                result = self.client.publish(topic, message, qos=qos, retain=retain)
                status = result[0]
                if status == 0:
                    if self.enable_logs:
                        logger.debug(f"[{self.client_id}] Published to '{topic}': {message[:100]}")
                    return True
                else:
                    logger.warning(f"[{self.client_id}] Failed to publish to '{topic}', status: {status}")
                    return False
            except Exception as e:
                logger.error(f"[{self.client_id}] Error publishing message: {e}")
                return False
        else:
            logger.warning(f"[{self.client_id}] Not connected, message not published to '{topic}'")
            return False

    def publish_json(self, topic: str, data: dict, qos: int = 0, retain: bool = False):
        """Publish JSON data to a topic"""
        try:
            message = json.dumps(data)
            return self.publish(topic, message, qos, retain)
        except Exception as e:
            logger.error(f"[{self.client_id}] Error serializing JSON: {e}")
            return False

    def loop_start(self):
        """Start the network loop in a background thread"""
        self.client.loop_start()
        if self.enable_logs:
            logger.info(f"[{self.client_id}] Started MQTT loop")

    def loop_stop(self):
        """Stop the network loop"""
        self.client.loop_stop()
        if self.enable_logs:
            logger.info(f"[{self.client_id}] Stopped MQTT loop")

    def loop_forever(self):
        """Run the network loop in the main thread (blocking)"""
        logger.info(f"[{self.client_id}] Starting MQTT loop (blocking)")
        self.client.loop_forever()
