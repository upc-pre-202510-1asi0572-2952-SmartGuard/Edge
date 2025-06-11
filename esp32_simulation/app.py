import paho.mqtt.client as mqtt
import json
import time

def simulate_event(user_id="alejandro"):
    client = mqtt.Client()
    client.connect("localhost", 1883, 60)
    payload = json.dumps({
        "user_id": user_id,
        "method": "FACE_RECOGNITION"
    })
    client.publish("esp32/door", payload)
    print(f"Publicado: {payload}")
    client.disconnect()

if __name__ == "__main__":
    simulate_event("alejandro")  # usuario válido
    time.sleep(2)
    simulate_event("intruso")    # usuario inválido
