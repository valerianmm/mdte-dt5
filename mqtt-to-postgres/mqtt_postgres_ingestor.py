import ast
import psycopg2
import paho.mqtt.client as mqtt

# ─── MQTT Config ─────────────────────────────────────────────
MQTT_BROKER = "mosquitto"   # Docker service name
MQTT_PORT = 1883
MQTT_TOPIC = "imu/data"

# ─── PostgreSQL Config ───────────────────────────────────────
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="iotdata",
    user="postgres",
    password="password"
)
print("Connected!", conn)
conn.close()


# MATCHES your schema exactly:
# timestamp BIGINT
# sample_id INTEGER
# ax, ay, az FLOAT
# gx, gy, gz FLOAT
INSERT_SQL = """
INSERT INTO imu_data (
    timestamp,
    sample_id,
    ax, ay, az,
    gx, gy, gz
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""

# ─── MQTT Version 2 Callbacks ────────────────────────────────
def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected to MQTT broker with code:", reason_code)
    client.subscribe(MQTT_TOPIC)
    print(f"Subscribed to {MQTT_TOPIC}")

def on_message(client, userdata, msg):
    print("\n================ NEW MESSAGE ================")
    print("Raw payload:", msg.payload)

    try:
        payload_string = msg.payload.decode()
        print("Decoded string:", payload_string)

        samples = ast.literal_eval(payload_string)
        print("Parsed samples:", samples)
        print("Number of samples:", len(samples))

        for index, s in enumerate(samples):
            print(f"\n--- Sample {index} ---")
            print("Sample data:", s)
            print("Length:", len(s))

            if len(s) != 8:
                print("❌ WRONG LENGTH → expected 8 values")
                continue

            print("Trying SQL insert with values:")
            print(tuple(s))

            try:
                cursor.execute(INSERT_SQL, tuple(s))
                print("✔ Insert OK")
            except Exception as sql_error:
                print("❌ SQL error:", sql_error)
                print("Attempted tuple:", tuple(s))
                print("SQL:", INSERT_SQL)

        conn.commit()
        print("✔ COMMIT OK")

    except Exception as e:
        print("❌ GENERAL ERROR:", e)
        print("Raw payload (again):", msg.payload)
        print("Decoded:", payload_string)


# ─── Start MQTT Client ───────────────────────────────────────
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT)
print("🚀 MQTT → PostgreSQL Ingestor Started...")
client.loop_forever()
