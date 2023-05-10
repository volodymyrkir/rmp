from typing import Callable

from paho.mqtt import client as mqtt_client

BROKER = 'broker.emqx.io'
PORT = 1883
topic_listen = "volodymyrkir/receive"
topic_publish = "volodymyrkir/publish"

client_id = 'python_client'
username = 'volodymyr'
password = 'Pythondev1'


class MqttConnector:
    def __init__(self,
                 user: str = username,
                 pw: str = password,
                 broker=BROKER,
                 port=PORT):
        self.client = self._connect_mqtt(user, pw, broker, port)
        self.client.loop_start()

    @staticmethod
    def _connect_mqtt(user, pw, broker, port):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)

        client = mqtt_client.Client(client_id)
        client.username_pw_set(user, pw)
        client.on_connect = on_connect
        client.connect(broker, port)
        return client

    def subscribe_client(self, on_message: Callable, topic=topic_listen):

        self.client.subscribe(topic)
        self.client.on_message = on_message

    def client_publish(self, value, topic=topic_publish):
        self.client.publish(topic, value)
