from data.topics import SQL_WRITE, SQL_READ
from services.mqtt import MQTTReceiver


class Database:
    def __init__(self):
        self.mqtt_client = MQTTReceiver(topics=(SQL_WRITE, SQL_READ))
        self.mqtt_client.db_handler.init_db()

    def start(self):
        self.mqtt_client.connect_and_run()

    def stop(self):
        self.mqtt_client.stop_client()

if __name__ == '__main__':
    database = Database()
    database.start()
