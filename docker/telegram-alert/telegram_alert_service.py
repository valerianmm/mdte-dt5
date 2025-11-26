import json
import os
from datetime import datetime

import paho.mqtt.client as mqtt
import requests

MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "fallsensor/predictor/alert")
MQTT_QOS = int(os.getenv("MQTT_QOS", "1"))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_API_URL = os.getenv("TELEGRAM_API_URL") or f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


def send_telegram_alert(message: str) -> bool:
    if not TELEGRAM_BOT_TOKEN:
        print("⚠️ TELEGRAM_BOT_TOKEN not set; skipping alert")
        return False
    if not TELEGRAM_CHAT_ID:
        print("⚠️ TELEGRAM_CHAT_ID not set; skipping alert")
        return False

    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        resp = requests.post(TELEGRAM_API_URL, data=payload, timeout=15)
        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        if resp.status_code == 200 and data.get("ok"):
            print(f"✅ Telegram alert sent to chat {TELEGRAM_CHAT_ID}")
            return True
        print(f"⚠️ Telegram response ({resp.status_code}): {resp.text}")
        return False
    except Exception as exc:
        print(f"❌ Failed to send Telegram alert: {exc}")
        return False


def format_timestamp(value: str | None) -> str:
    if not value or value == "unknown time":
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    candidate = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(candidate)
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        parts = candidate.split(":")
        if len(parts) >= 2:
            return ":".join(parts[:2])
        return candidate


def format_alert(payload: dict) -> str:
    prob = payload.get("probability")
    prob_text = f"{prob:.2f}" if isinstance(prob, (int, float)) else "N/A"
    timestamp = format_timestamp(payload.get("timestamp"))
    sample_id = payload.get("last_sample_id", "N/A")
    return (
        "🚨 Fall detected!\n"
        f"  Timestamp: {timestamp}"
    )


def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"Connected to MQTT broker {MQTT_BROKER}:{MQTT_PORT} rc={reason_code}")
    client.subscribe(MQTT_TOPIC, qos=MQTT_QOS)
    print(f"Subscribed to topic '{MQTT_TOPIC}' (QoS={MQTT_QOS})")


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        print(f"Received fall alert payload: {data}")
    except json.JSONDecodeError:
        print("⚠️ Received non-JSON payload; skipping.")
        return

    send_telegram_alert(format_alert(data))


def main():
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_forever()


if __name__ == "__main__":
    main()


