import time
import json
import random
import paho.mqtt.client as mqtt

MQTT_BROKER = "mosquitto"
MQTT_PORT = 1883
MQTT_TOPIC = "arduino/imu"

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

def generate_sensor_data():
    # Simulate 3-axis gyroscope and accelerometer, rounded to 2 decimal places
    data = {
        "timestamp": round(time.time(), 2),
        "gym": {
            "x": round(random.uniform(-250, 250), 2),
            "y": round(random.uniform(-250, 250), 2),
            "z": round(random.uniform(-250, 250), 2)
        },
        "acc": {
            "x": round(random.uniform(-2, 2), 2),
            "y": round(random.uniform(-2, 2), 2),
            "z": round(random.uniform(-2, 2), 2)
        }
    }
    return data

if __name__ == "__main__":
    while True:
        payload = json.dumps(generate_sensor_data())
        client.publish(MQTT_TOPIC, payload)
        print(f"Published: {payload}")
        time.sleep(0.5)
