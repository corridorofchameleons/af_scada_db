from pathlib import Path

import orjson
import paho.mqtt.client as mqtt

from db.db_handler import DBHandler

DB_FOLDER = Path(__file__).resolve().parent.parent / 'data'
DB_NAME = 'values.db'

class MQTTReceiver:
    def __init__(
            self,
            host='localhost',
            port=1883,
            topics: tuple[str, ...] = None
    ):
        self.topics = topics

        self.host = host
        self.port = port

        self.db_handler = DBHandler(DB_FOLDER, DB_NAME)

        self.client = mqtt.Client(
            client_id='receive_client',
            protocol=mqtt.MQTTv5,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

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
        print(data)
        if data is not None:
            data_to_write = data.get('data')
            self.db_handler.save_data(data_to_write)

    @staticmethod
    def _parse_payload(payload_bytes):
        try:
            return orjson.loads(payload_bytes.decode('utf-8'))
        except Exception:
            return None