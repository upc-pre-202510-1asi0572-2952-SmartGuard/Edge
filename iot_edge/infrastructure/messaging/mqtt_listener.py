import json
import paho.mqtt.client as mqtt

class MQTTListener:
    def __init__(self, use_case):
        self.use_case = use_case

    def on_connect(self, client, userdata, flags, rc):
        print("Connected to MQTT")
        client.subscribe("esp32/door")

    def on_message(self, client, userdata, msg):
        data = json.loads(msg.payload.decode())
        user_id = data.get("user_id")
        method = data.get("method", "FACE_RECOGNITION")
        event = self.use_case.execute(user_id, method)
        print(f"[{event.timestamp}] {event.user_id} - {event.result}")

    def start(self):
        client = mqtt.Client()
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.connect("localhost", 1883, 60)
        client.loop_forever()