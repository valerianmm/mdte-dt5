"""
Poll PostgreSQL for new IMU samples, build 2s sliding windows, and publish
fall predictions to MQTT so downstream services (e.g., whatsapp-alert) can react.
"""

import json
import os
import sys
import time
from datetime import timedelta
from pathlib import Path
from typing import List, Tuple

import numpy as np
import paho.mqtt.client as mqtt
import psycopg2

# Local helper module copied into the container at build time
import ai_model_utils as mu


# ─── Settings (env overrides are supported) ──────────────────────────────────
PG_HOST = os.getenv("PG_HOST", "postgres")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DB = os.getenv("PG_DB", "iotdata")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "password")

MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "fallsensor/predictor/alert")
MQTT_QOS = int(os.getenv("MQTT_QOS", "1"))

SAMPLE_RATE_HZ = int(os.getenv("SAMPLE_RATE_HZ", "27"))  # device runs at ~27 Hz
WINDOW_SECONDS = float(os.getenv("WINDOW_SECONDS", "4.5"))  # ~120 samples per window
HISTORY_SECONDS = float(os.getenv("HISTORY_SECONDS", "6.0"))  # keep slightly more than one window buffered
POLL_INTERVAL_SECONDS = float(os.getenv("POLL_INTERVAL_SECONDS", "0.25"))
MODEL_PATH = Path(os.getenv("MODEL_PATH", "/app/best_xgb_model.joblib"))
SCALER_PATH = Path(os.getenv("SCALER_PATH", "/app/scaler.joblib"))

# Thresholding / debounce to reduce false positives
MIN_PROBABILITY = float(os.getenv("MIN_PROBABILITY", "0.70"))
REQUIRED_CONSECUTIVE = int(os.getenv("REQUIRED_CONSECUTIVE", "2"))
CLEAR_COOLDOWN_SECONDS = float(os.getenv("CLEAR_COOLDOWN_SECONDS", "5.0"))
LOG_PUBLISH = os.getenv("LOG_PUBLISH", "false").lower() == "true"
EVENT_COOLDOWN_SECONDS = float(os.getenv("EVENT_COOLDOWN_SECONDS", "10.0"))


def connect_db():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
    )


def connect_mqtt():
    # Use the newer callback API version to silence deprecation warnings
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start()
    return client


def fetch_rows(cursor) -> List[Tuple]:
    query = """
    SELECT sample_id, ax, ay, az, gx, gy, gz, received_at
    FROM imu_data
    WHERE received_at >= NOW() - INTERVAL %s
    ORDER BY received_at ASC;
    """
    interval = f"{HISTORY_SECONDS} seconds"
    cursor.execute(query, (interval,))
    return cursor.fetchall()


def main():
    print(f"Loading model from {MODEL_PATH} and scaler from {SCALER_PATH}")
    model, scaler = mu.load_model_artifacts(model_path=MODEL_PATH, scaler_path=SCALER_PATH)

    mqtt_client = connect_mqtt()
    print(f"Connected to MQTT at {MQTT_BROKER}:{MQTT_PORT}, publishing to topic '{MQTT_TOPIC}' (QoS={MQTT_QOS})", flush=True)

    conn = connect_db()
    conn.autocommit = True
    cursor = conn.cursor()
    print(f"Connected to Postgres at {PG_HOST}:{PG_PORT} (db={PG_DB})", flush=True)

    consecutive_positive = 0
    last_publish_time = 0.0

    while True:
        try:
            rows = fetch_rows(cursor)
            if rows:
                latest_ts = rows[-1][-1]
                cutoff = latest_ts - timedelta(seconds=WINDOW_SECONDS)
                window_rows = [r for r in rows if r[-1] >= cutoff]

                if len(window_rows) >= 2:
                    samples = np.array(
                        [[ax, ay, az, gx, gy, gz] for _, ax, ay, az, gx, gy, gz, _ in window_rows],
                        dtype=float,
                    )
                    feats = mu.extract_features_signal(samples, fs=SAMPLE_RATE_HZ)
                    feats_scaled = scaler.transform(feats)
                    pred = int(model.predict(feats_scaled)[0])
                    proba = None
                    if hasattr(model, "predict_proba"):
                        proba = float(model.predict_proba(feats_scaled)[0, 1])
                    if LOG_PUBLISH:
                        print(
                            f"Window size: {len(window_rows)} samples -> predicting... prob={proba}",
                            flush=True,
                        )

                    if pred == 1 and (proba is None or proba >= MIN_PROBABILITY):
                        consecutive_positive += 1
                    else:
                        consecutive_positive = 0

                    should_publish = (
                        pred == 1
                        and consecutive_positive >= REQUIRED_CONSECUTIVE
                        and (time.time() - last_publish_time) >= CLEAR_COOLDOWN_SECONDS
                    )

                    if should_publish:
                        payload = {
                            "prediction": 1,
                            "probability": proba,
                            "last_sample_id": window_rows[-1][0],
                            "window_seconds": WINDOW_SECONDS,
                            "generated_at_ms": int(time.time() * 1000),
                            "timestamp": window_rows[-1][-1].isoformat() if window_rows[-1][-1] else None,
                        }
                        mqtt_client.publish(MQTT_TOPIC, json.dumps(payload), qos=MQTT_QOS)
                        last_publish_time = time.time()
                        if LOG_PUBLISH:
                            print(
                                f"Published FALL prediction prob={proba} at sample_id={window_rows[-1][0]} "
                                f"(consec={consecutive_positive})"
                            )
                elif LOG_PUBLISH:
                    print("Not enough samples in window yet.", flush=True)

            time.sleep(POLL_INTERVAL_SECONDS)

        except (psycopg2.OperationalError, psycopg2.InterfaceError) as db_err:
            print(f"Database connection lost: {db_err} -> reconnecting...")
            time.sleep(1.0)
            conn = connect_db()
            conn.autocommit = True
            cursor = conn.cursor()
        except Exception as exc:
            print(f"Error in polling loop: {exc}")
            time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
