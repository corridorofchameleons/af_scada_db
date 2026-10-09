from pathlib import Path

import orjson
import paho.mqtt.client as mqtt
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
        self.db_handler.init_db()
        print("[WORKER] SQL MQTT started")
        try:
            self.client.connect(self.host, self.port, 60)
            self.client.loop_forever()
        except Exception as e:
            print(f"[WORKER] SQL MQTT Network error: {e}")

    def _on_connect(self, client, userdata, flags, rc, props=None):
        if rc == 0:
            print("[WORKER] SQL MQTT Connected to broker")
            for topic in self.topics:
                client.subscribe(topic, qos=0)
        else:
            print(f"[WORKER] SQL MQTT Connect failed with code {rc}")

    def _on_disconnect(self, client, userdata, reason_code,
                       properties=None):
        if reason_code == 0:
            print("[MQTT] Disconnected cleanly.")
        else:
            print(f"[MQTT] Unexpected disconnect. Reason: {reason_code}")
            print("[MQTT] Attempting to reconnect...")

    def stop_client(self):
        print("[RECEIVER] Stopping...")
        try:
            sock = self.client.socket()
            if sock:
                sock.close()
        except Exception:
            pass
        self.client.disconnect()

    def _on_message(self, client, userdata, msg):
        topic: str = msg.topic
        data = self._parse_payload(msg.payload)
        print(f'[IN] SQL MQTT Recieved from {topic}: {data}')
        if topic == SQL_WRITE:
            print(data)
            if data is not None:
                data_to_write = data.get('data')
                self.db_handler.save_data(data_to_write)
        elif topic == SQL_READ:
            data = self.db_handler.get_data(data)
            self.publish_data(data)

    def publish_data(self, data: dict):
        topic = self.publish_topic
        json_bytes = orjson.dumps(data)
        result = self.client.publish(
            topic=topic,
            payload=json_bytes,
            qos=1,
            retain=False
        )
        success = True if result.rc == MQTTErrorCode.MQTT_ERR_SUCCESS else False
        if success:
            print(f"[OUT] SQL MQTT Sent to {topic}: {data}")
        else:
            print(f"FAILED to send message to {topic}")

    @staticmethod
    def _parse_payload(payload_bytes):
        try:
            return orjson.loads(payload_bytes.decode('utf-8'))
        except Exception:
            return None