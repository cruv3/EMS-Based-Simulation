from paho.mqtt.client import Client
from asyncio import run

class MQTTReceiver:
    def __init__(self, broker_address, topic, on_message_callback=None):
        self.broker_address = broker_address
        self.topic = topic
        self.on_message_callback = on_message_callback

        self.client = Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        print(f"MQTT connected with result code {rc}")
        self.client.subscribe(self.topic)

    def _on_message(self, client, userdata, msg):
        message = msg.payload.decode()
        print(f"Recveived MQTT: {message}")

        if self.on_message_callback:
            self.on_message_callback(message)

        # # Send BLE message
        # try:
        #     if self.ble_handler and self.ble_handler.client.is_connected:
        #         run(self.ble_handler.send(message))
        #     else:
        #         print("BLE not connected.")
        # except Exception as e:
        #     print("Failed to send over BLE:", e)

    def start(self):
        self.client.connect(self.broker_address)
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
