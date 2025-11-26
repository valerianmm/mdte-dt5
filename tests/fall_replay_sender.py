"""
Replay a fall CSV over MQTT at a fixed sample rate so it flows through the ingest → Postgres path.
Each MQTT message is a single-sample list to match mqtt_postgres_ingestor expectations.
"""

import os
import time
import ast
import json
from pathlib import Path

import pandas as pd
import paho.mqtt.client as mqtt

MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "imu/data")

FALL_CSV_PATH = Path(os.getenv("FALL_CSV_PATH", "/app/fall.csv"))
WALK_CSV_PATH = Path(os.getenv("WALK_CSV_PATH", "/app/walk.csv"))
SAMPLE_RATE_HZ = float(os.getenv("SAMPLE_RATE_HZ", "27"))
SLEEP_SECONDS = 1.0 / SAMPLE_RATE_HZ if SAMPLE_RATE_HZ > 0 else 0.04
LOOP_DELAY_SECONDS = float(os.getenv("LOOP_DELAY_SECONDS", "0.0"))


def load_csv(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"CSV not found at {path}")

    df = pd.read_csv(path)
    required = ["t", "acc_x", "acc_y", "acc_z", "gyro_x", "gyro_y", "gyro_z"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing column '{col}' in {path}")
    return df


def sample_from_row(row, offset):
    return [
        int(row["t"]) + offset,
        0,  # sample_id placeholder
        float(row["acc_x"]),
        float(row["acc_y"]),
        float(row["acc_z"]),
        float(row["gyro_x"]),
        float(row["gyro_y"]),
        float(row["gyro_z"]),
    ]


def main():
    fall_df = load_csv(FALL_CSV_PATH)
    walk_df = load_csv(WALK_CSV_PATH)

    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start()
    print(f"Connected to MQTT {MQTT_BROKER}:{MQTT_PORT}, sending to topic '{MQTT_TOPIC}'")

    next_sample_id = 1
    while True:
        for seq_name, df in [("fall", fall_df)]:
            rows_sent = 0
            for _, row in df.iterrows():
                sample = [
                    int(row["t"]),
                    next_sample_id,
                    float(row["acc_x"]),
                    float(row["acc_y"]),
                    float(row["acc_z"]),
                    float(row["gyro_x"]),
                    float(row["gyro_y"]),
                    float(row["gyro_z"]),
                ]
                next_sample_id += 1

                payload = str([sample])
                client.publish(MQTT_TOPIC, payload)
                rows_sent += 1
                if rows_sent % 10 == 0 or rows_sent == len(df):
                    print(f"{seq_name}: Sent {rows_sent}/{len(df)} samples")
                time.sleep(SLEEP_SECONDS)
            print(f"{seq_name} sequence complete.")

        print(f"Cycle complete. Sleeping {LOOP_DELAY_SECONDS}s before next cycle.")
        time.sleep(LOOP_DELAY_SECONDS)

    # not reached in continuous loop
    # client.loop_stop()
    # client.disconnect()


if __name__ == "__main__":
    main()
