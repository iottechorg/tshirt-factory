import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT
import logging


class MQTTPublisher:
    def __init__(self, client_id, enable_logs=False):
        self.client = mqtt.Client(client_id)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.is_connected = False
        self.enable_logs = enable_logs

    def connect(self):
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
        except Exception as e:
            logging.error(f"Error while connecting: {e}")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            if self.enable_logs:
                logging.info("Connected to MQTT Broker!")
            self.is_connected = True
        else:
            logging.error(f"Failed to connect, return code {rc}")

    def on_disconnect(self, client, userdata, rc):
        self.is_connected = False
        if rc != 0:
            logging.info(f"Disconnected unexpectedly with code: {rc}")

    def publish(self, topic, message):
        if self.is_connected:
            try:
                result = self.client.publish(topic, message)
                status = result[0]
                if status == 0:
                    if self.enable_logs:
                        logging.info(f"Published to topic '{topic}': {message}")
                else:
                    logging.warning(f"Failed to publish to topic '{topic}': {message}")
            except Exception as e:
                logging.error(f"Error publishing message: {e}")
        else:
            logging.warning("MQTT client not connected. Message not published.")

    def loop_start(self):
        self.client.loop_start()

    def loop_stop(self):
        self.client.loop_stop()
