#include "mqtt_manager.h"
#include "wifi_manager.h"
#include "logger.h"
#include "credentials.h"
#include "imu_manager.h"   // get IMU_BUFFER_ROWS, imuBuffer, imuTail, etc.
#include <PubSubClient.h>
#include <WiFiS3.h>

#define MQTT_PORT             1883
#define MQTT_TOPIC            "imu/data"
#define USER_BATCH_SIZE       5
#define MQTT_SEND_PERIOD_MS   200

static WiFiClient wifiClient;
static PubSubClient mqttClient(wifiClient);
static char payload[512];   // reduced from 800 to lower RAM usage
unsigned long lastSend = 0;

void mqttConnect() {
  const char *host = knownNetworks[0].mqtt_host;
  mqttClient.setServer(host, MQTT_PORT);
  while (!mqttClient.connected()) {
    String id = "ModulinoIMU-" + String(random(0xffff), HEX);
    if (mqttClient.connect(id.c_str())) {
      LOG_INFO("✅ MQTT connected (%s)", id.c_str());
    } else {
      LOG_WARN("MQTT reconnect...");
      delay(500);
    }
  }
}

void mqttLoop() {
  mqttClient.loop();
}

void mqttPublishSamples(IMUData *samples, int count) {
  char numbuf[16];
  int idx = 0;
  payload[idx++] = '[';

  for (int i = 0; i < count; i++) {
    IMUData &d = samples[i];
    payload[idx++] = '[';
    idx += sprintf(payload + idx, "%lu,", d.t);
    idx += sprintf(payload + idx, "%lu,", (unsigned long)d.msgId);
    dtostrf(d.ax, 0, 2, numbuf); idx += sprintf(payload + idx, "%s,", numbuf);
    dtostrf(d.ay, 0, 2, numbuf); idx += sprintf(payload + idx, "%s,", numbuf);
    dtostrf(d.az, 0, 2, numbuf); idx += sprintf(payload + idx, "%s,", numbuf);
    dtostrf(d.gx, 0, 2, numbuf); idx += sprintf(payload + idx, "%s,", numbuf);
    dtostrf(d.gy, 0, 2, numbuf); idx += sprintf(payload + idx, "%s,", numbuf);
    dtostrf(d.gz, 0, 2, numbuf); idx += sprintf(payload + idx, "%s", numbuf);
    payload[idx++] = ']';
    if (i < count - 1) payload[idx++] = ',';
  }
  payload[idx++] = ']';
  payload[idx] = '\0';
  mqttClient.publish(MQTT_TOPIC, payload);
}

void mqttSendBuffer() {
  if (WiFi.status() != WL_CONNECTED || !mqttClient.connected()) return;
  int count = imuBufferCount();
  if (count < USER_BATCH_SIZE) return;

  IMUData samples[USER_BATCH_SIZE];
  for (int i = 0; i < USER_BATCH_SIZE; i++) {
    samples[i] = imuBuffer[imuTail];
    imuTail = (imuTail + 1) % IMU_BUFFER_ROWS;
  }
  mqttPublishSamples(samples, USER_BATCH_SIZE);
}

void mqttPeriodicSend() {
  if (millis() - lastSend > MQTT_SEND_PERIOD_MS) {
    mqttSendBuffer();
    lastSend = millis();
  }
}
