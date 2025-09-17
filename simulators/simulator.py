import time, random, json
import paho.mqtt.client as mqtt

BROKER = "localhost"   # change if broker is in Docker with another host/IP
PORT = 1883
TOPIC = "imu/data"

client = mqtt.Client()
client.connect(BROKER, PORT, 60)

while True:
    imu_data = {
        "timestamp": time.time(),
        "accel": {
            "x": round(random.uniform(-2, 2), 3),
            "y": round(random.uniform(-2, 2), 3),
            "z": round(random.uniform(8, 10), 3)
        },
        "gyro": {
            "x": round(random.uniform(-250, 250), 2),
            "y": round(random.uniform(-250, 250), 2),
            "z": round(random.uniform(-250, 250), 2)
        }
    }
    client.publish(TOPIC, json.dumps(imu_data))
    print("Published:", imu_data)
    time.sleep(1)
