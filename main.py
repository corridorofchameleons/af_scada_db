from data.topics import SQL_WRITE
from services.mqtt import MQTTReceiver


class Database:
    def __init__(self):
        self.mqtt_client = MQTTReceiver(topics=(SQL_WRITE,))
        self.mqtt_client.db_handler.init_db()
        # data = self.mqtt_client.db_handler.get_data()
        # print(data)

    def start(self):
        self.mqtt_client.connect_and_run()

    def stop(self):
        self.mqtt_client.stop_client()

if __name__ == '__main__':
    database = Database()
    database.start()
