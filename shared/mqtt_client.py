"""
Enhanced MQTT client with subscription support and better error handling
Updated for latest paho-mqtt version compatibility
"""
import paho.mqtt.client as mqtt
import logging
import json
import time
import ssl
import re
from typing import Callable, Optional, Dict, Any

logger = logging.getLogger(__name__)


def mqtt_topic_matches(subscription: str, topic: str) -> bool:
    """
    Check if a topic matches a subscription pattern with wildcards.
    + matches a single level
    # matches multiple levels
    """
    # Convert MQTT wildcards to regex
    pattern = subscription.replace('+', '[^/]+').replace('#', '.*')
    pattern = f'^{pattern}$'
    return re.match(pattern, topic) is not None


class MQTTClientWrapper:
    """Enhanced MQTT client for both publishing and subscribing"""

    def __init__(self, client_id: str, broker: str, port: int = 1883,
                 keepalive: int = 60, enable_logs: bool = True,
                 username: Optional[str] = None, password: Optional[str] = None,
                 use_tls: bool = False, ca_certs: Optional[str] = None):
        self.client_id = client_id
        self.broker = broker
        self.port = port
        self.keepalive = keepalive
        self.enable_logs = enable_logs
        self.is_connected = False
        self.subscriptions = {}  # topic -> callback mapping
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.ca_certs = ca_certs

        # Create MQTT client with updated parameter handling
        self.client = mqtt.Client(
            client_id=client_id,
            protocol=mqtt.MQTTv311,  # Use MQTT v3.1.1 for better compatibility
            clean_session=True
        )
        
        # Set up callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        self.client.on_subscribe = self._on_subscribe
        self.client.on_unsubscribe = self._on_unsubscribe
        self.client.on_log = self._on_log

        # Set credentials if provided
        if username and password:
            self.client.username_pw_set(username, password)

        # Configure TLS if required
        if use_tls:
            self._configure_tls()

    def _configure_tls(self):
        """Configure TLS/SSL settings"""
        try:
            if self.ca_certs:
                self.client.tls_set(
                    ca_certs=self.ca_certs,
                    cert_reqs=ssl.CERT_REQUIRED,
                    tls_version=ssl.PROTOCOL_TLS
                )
            else:
                self.client.tls_set()
            self.client.tls_insecure_set(False)  # Always verify certificate
        except Exception as e:
            logger.error(f"[{self.client_id}] Failed to configure TLS: {e}")
            raise

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Callback when connection is established"""
        if rc == 0:
            self.is_connected = True
            if self.enable_logs:
                logger.info(f"[{self.client_id}] Connected to MQTT Broker at {self.broker}:{self.port}")
                logger.debug(f"[{self.client_id}] Connection flags: {flags}")

            # Re-subscribe to all topics after reconnection
            for topic, callback_info in self.subscriptions.items():
                qos_level = callback_info.get('qos', 0)
                result, mid = self.client.subscribe(topic, qos_level)
                if result == mqtt.MQTT_ERR_SUCCESS:
                    logger.info(f"[{self.client_id}] ✓ Re-subscribed to topic: {topic} (QoS: {qos_level})")
                else:
                    logger.error(f"[{self.client_id}] ✗ Failed to re-subscribe to topic: {topic}, error: {result}")
        else:
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorised"
            }
            error_msg = error_messages.get(rc, f"Unknown error code: {rc}")
            logger.error(f"[{self.client_id}] Failed to connect: {error_msg}")

    def _on_disconnect(self, client, userdata, rc, properties=None):
        """Callback when disconnected"""
        self.is_connected = False
        if rc != 0:
            logger.warning(f"[{self.client_id}] Disconnected unexpectedly with code: {rc}")
            # Attempt automatic reconnection
            self._handle_reconnection()
        else:
            if self.enable_logs:
                logger.info(f"[{self.client_id}] Disconnected from MQTT Broker")

    def _on_message(self, client, userdata, msg):
        """Callback when message is received"""
        topic = msg.topic
        payload = msg.payload.decode('utf-8')

        if self.enable_logs:
            logger.info(f"[{self.client_id}] ✓ RECEIVED message on topic '{topic}': {payload[:200]}")

        # Match topic against all subscription patterns (including wildcards)
        matched = False
        for sub_pattern, callback_info in self.subscriptions.items():
            if mqtt_topic_matches(sub_pattern, topic):
                matched = True
                try:
                    logger.info(f"[{self.client_id}] ✓ Matched pattern '{sub_pattern}' - invoking callback")
                    callback_info['callback'](topic, payload)
                except Exception as e:
                    logger.error(f"[{self.client_id}] ✗ Error in message callback for topic '{topic}': {e}", exc_info=True)
        
        if not matched:
            logger.warning(f"[{self.client_id}] ⚠ Message received but no subscription matched topic '{topic}'")

    def _on_publish(self, client, userdata, mid):
        """Callback when message is published"""
        if self.enable_logs:
            logger.debug(f"[{self.client_id}] Message published with mid: {mid}")

    def _on_subscribe(self, client, userdata, mid, granted_qos, properties=None):
        """Callback when subscription is successful"""
        if self.enable_logs:
            logger.debug(f"[{self.client_id}] Subscription confirmed with mid: {mid}, granted QoS: {granted_qos}")

    def _on_unsubscribe(self, client, userdata, mid, properties=None):
        """Callback when unsubscription is successful"""
        if self.enable_logs:
            logger.debug(f"[{self.client_id}] Unsubscription confirmed with mid: {mid}")

    def _on_log(self, client, userdata, level, buf):
        """Callback for MQTT logging"""
        if self.enable_logs:
            log_levels = {
                mqtt.MQTT_LOG_INFO: logging.INFO,
                mqtt.MQTT_LOG_NOTICE: logging.INFO,
                mqtt.MQTT_LOG_WARNING: logging.WARNING,
                mqtt.MQTT_LOG_ERR: logging.ERROR,
                mqtt.MQTT_LOG_DEBUG: logging.DEBUG
            }
            logger.log(log_levels.get(level, logging.INFO), f"[{self.client_id}] MQTT Log: {buf}")

    def _handle_reconnection(self):
        """Handle automatic reconnection with backoff"""
        if self.enable_logs:
            logger.info(f"[{self.client_id}] Attempting automatic reconnection...")
        time.sleep(2)  # Wait before reconnecting
        self.connect(retry_count=3, retry_delay=2)

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

    def subscribe(self, topic: str, callback: Callable[[str, str], None], qos: int = 0):
        """Subscribe to a topic with a callback function and QoS level"""
        self.subscriptions[topic] = {'callback': callback, 'qos': qos}
        if self.is_connected:
            result, mid = self.client.subscribe(topic, qos)
            if result == mqtt.MQTT_ERR_SUCCESS:
                if self.enable_logs:
                    logger.info(f"[{self.client_id}] Subscribed to topic: {topic} with QoS: {qos}")
                return True
            else:
                logger.error(f"[{self.client_id}] Failed to subscribe to '{topic}', error: {result}")
                return False
        else:
            logger.warning(f"[{self.client_id}] Not connected, subscription to '{topic}' will be applied on connect")
            return False

    def unsubscribe(self, topic: str):
        """Unsubscribe from a topic"""
        if topic in self.subscriptions:
            if self.is_connected:
                result, mid = self.client.unsubscribe(topic)
                if result == mqtt.MQTT_ERR_SUCCESS:
                    del self.subscriptions[topic]
                    if self.enable_logs:
                        logger.info(f"[{self.client_id}] Unsubscribed from topic: {topic}")
                    return True
                else:
                    logger.error(f"[{self.client_id}] Failed to unsubscribe from '{topic}', error: {result}")
                    return False
            else:
                del self.subscriptions[topic]
                logger.warning(f"[{self.client_id}] Not connected, unsubscription from '{topic}' will be applied on connect")
                return False
        return True

    def publish(self, topic: str, message, qos: int = 0, retain: bool = False) -> bool:
        """Publish a message to a topic (auto-converts dict to JSON)"""
        if not self.is_connected:
            logger.warning(f"[{self.client_id}] Not connected, message not published to '{topic}'")
            return False
        
        try:
            # Auto-convert dict to JSON string
            if isinstance(message, dict):
                payload = json.dumps(message, ensure_ascii=False)
            else:
                payload = message
            
            msg_info = self.client.publish(topic, payload, qos=qos, retain=retain)
            if msg_info.rc == mqtt.MQTT_ERR_SUCCESS:
                if self.enable_logs:
                    logger.debug(f"[{self.client_id}] Published to '{topic}': {str(payload)[:100]}")
                return True
            else:
                logger.warning(f"[{self.client_id}] Failed to publish to '{topic}', error: {msg_info.rc}")
                return False
        except Exception as e:
            logger.error(f"[{self.client_id}] Error publishing message: {e}")
            return False

    def publish_json(self, topic: str, data: Dict[str, Any], qos: int = 0, retain: bool = False) -> bool:
        """Publish JSON data to a topic"""
        try:
            message = json.dumps(data, ensure_ascii=False)
            return self.publish(topic, message, qos, retain)
        except Exception as e:
            logger.error(f"[{self.client_id}] Error serializing JSON: {e}")
            return False

    def loop_start(self):
        """Start the network loop in a background thread"""
        try:
            self.client.loop_start()
            if self.enable_logs:
                logger.info(f"[{self.client_id}] Started MQTT loop")
        except Exception as e:
            logger.error(f"[{self.client_id}] Error starting MQTT loop: {e}")

    def loop_stop(self):
        """Stop the network loop"""
        try:
            self.client.loop_stop()
            if self.enable_logs:
                logger.info(f"[{self.client_id}] Stopped MQTT loop")
        except Exception as e:
            logger.error(f"[{self.client_id}] Error stopping MQTT loop: {e}")

    def loop_forever(self):
        """Run the network loop in the main thread (blocking)"""
        logger.info(f"[{self.client_id}] Starting MQTT loop (blocking)")
        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            logger.info(f"[{self.client_id}] MQTT loop interrupted by user")
            self.disconnect()
        except Exception as e:
            logger.error(f"[{self.client_id}] Error in MQTT loop: {e}")

    def set_will(self, topic: str, payload: str, qos: int = 0, retain: bool = False):
        """Set Last Will and Testament message"""
        try:
            self.client.will_set(topic, payload, qos, retain)
            if self.enable_logs:
                logger.info(f"[{self.client_id}] Set LWT on topic: {topic}")
        except Exception as e:
            logger.error(f"[{self.client_id}] Error setting LWT: {e}")

    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self.is_connected

    def get_subscriptions(self) -> list:
        """Get list of subscribed topics"""
        return list(self.subscriptions.keys())