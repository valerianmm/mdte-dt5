import ast
import os
import psycopg2
import paho.mqtt.client as mqtt

# ─── MQTT Config ─────────────────────────────────────────────
MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")   # Docker service name
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "imu/data")

# ─── PostgreSQL Config ───────────────────────────────────────
PG_HOST = os.getenv("PG_HOST", "postgres")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DB = os.getenv("PG_DB", "iotdata")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "password")

conn = psycopg2.connect(
    host=PG_HOST,
    port=PG_PORT,
    database=PG_DB,
    user=PG_USER,
    password=PG_PASSWORD,
)
conn.autocommit = True
cursor = conn.cursor()
print(f"Connected to Postgres at {PG_HOST}:{PG_PORT}")


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
