import time
from pathlib import Path

import orjson
import paho.mqtt.client as mqtt
from loguru import logger
from paho.mqtt.enums import MQTTErrorCode

from data.topics import SQL_READ, SQL_WRITE, SQL_DATA
from db.db_handler import DBHandler

DB_FOLDER = Path(__file__).resolve().parent.parent / 'data'
DB_NAME = 'values.db'

class MQTTReceiver:
    def __init__(
            self,
            host='localhost',
            port=1883,
            topics: tuple[str, ...] = None,
            publish_topic: str = SQL_DATA
    ):
        self.topics = topics
        self.publish_topic = publish_topic

        self.host = host
        self.port = port

        self.db_handler = DBHandler(DB_FOLDER, DB_NAME)

        self.client = mqtt.Client(
            client_id='hybrid_worker',
            protocol=mqtt.MQTTv5,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        # self.client.on_disconnect = self._on_disconnect

    def connect_and_run(self):
        logger.info("[WORKER] Starting...")
        try:
            self.client.connect(self.host, self.port, 60)
            self.client.loop_forever()
        except Exception as e:
            logger.error(f"[WORKER] SQL MQTT Network error: {e}")

    def _on_connect(self, client, userdata, flags, rc, props=None):
        if rc == 0:
            logger.success("[WORKER] SQL MQTT Connected to broker")
            for topic in self.topics:
                client.subscribe(topic, qos=0)
        else:
            logger.error(f"[WORKER] SQL MQTT Connect failed with code {rc}")

    def _on_disconnect(self, client, userdata, reason_code,
                       properties=None):
        if reason_code == 0:
            logger.success("[MQTT] Disconnected cleanly.")
        else:
            logger.error(f"[MQTT] Unexpected disconnect. Reason: {reason_code}")
            print("[MQTT] Attempting to reconnect...")

    def stop_client(self):
        logger.info("[WORKER] Stopping...")
        try:
            sock = self.client.socket()
            if sock:
                sock.close()
                logger.success('[WORKER] socket closed')
        except Exception as e:
            logger.error(f'[WORKER] failed to stop correctly: {e}')
        self.client.disconnect()

    def _on_message(self, client, userdata, msg):
        topic: str = msg.topic
        data = self._parse_payload(msg.payload)
        logger.info(f'[IN] SQL MQTT Received from {topic}')
        if topic == SQL_WRITE:
            if data is not None:
                data_to_write = data.get('data')
                self.db_handler.save_data(data_to_write)
        elif topic == SQL_READ:
            data = self.db_handler.get_data(data)
            self.publish_data(data)

    def publish_data(self, data: dict):
        topic = self.publish_topic
        ts = int(time.time())
        payload = {
            'timestamp': ts,
            'data': data
        }
        json_bytes = orjson.dumps(payload)
        result = self.client.publish(
            topic=topic,
            payload=json_bytes,
            qos=1,
            retain=False
        )
        success = True if result.rc == MQTTErrorCode.MQTT_ERR_SUCCESS else False
        if success:
            logger.success(f"[OUT] SQL MQTT Sent to {topic} at int-ts: {ts}")
        else:
            logger.error(f"[OUT] FAILED to send message to {topic} at int-ts: {ts}")

    @staticmethod
    def _parse_payload(payload_bytes):
        try:
            return orjson.loads(payload_bytes.decode('utf-8'))
        except Exception as e:
            logger.error(f'FAILED TO PARSE JSON: {e}')
            return None