#include <Arduino.h>
#include <WiFiS3.h>
#include <PubSubClient.h>
#include "Modulino.h"
#include "credentials.h"
#include "logger.h"

// ─── User configuration ─────────────────────────────────────
#define MODE_CONTINUOUS   1   // Continuous sampling & publishing
#define MODE_TEST         2   // Benchmark / timing tests
#define ACTIVE_MODE       MODE_CONTINUOUS   // <── choose mode here

// ─── Config ─────────────────────────────────────────────────
#define MQTT_PORT        1883
#define MQTT_TOPIC       "imu/data"
#define SAMPLING_FREQ_HZ 25
#define BUFFER_ROWS      500
#define USER_BATCH_SIZE  5
#define MQTT_SEND_PERIOD_MS 200
#define MQTT_TEST_ITER   50

// ─── Globals ────────────────────────────────────────────────
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
ModulinoMovement imu;

struct IMUData {
  unsigned long t;
  float ax, ay, az;
  float gx, gy, gz;
};

IMUData buffer[BUFFER_ROWS];
uint16_t head = 0, tail = 0;
static char payload[800];
unsigned long nextSampleTime = 0;
unsigned long sampleIntervalUs = 1000000 / SAMPLING_FREQ_HZ;
unsigned long lastConnCheck = 0;

// ─── Wi-Fi & MQTT connect ───────────────────────────────────
void connectWiFi() {
  const char *ssid = knownNetworks[0].ssid;
  const char *pass = knownNetworks[0].password;
  WiFi.disconnect();
  WiFi.begin(ssid, pass);
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 8000) delay(200);
  if (WiFi.status() == WL_CONNECTED)
    LOG_INFO("✅ Wi-Fi connected: %s", WiFi.localIP().toString().c_str());
  else
    LOG_WARN("❌ Wi-Fi connect timeout");
}

void connectMQTT() {
  const char *host = knownNetworks[0].mqtt_host;
  mqttClient.setServer(host, MQTT_PORT);
  while (!mqttClient.connected()) {
    String id = "ModulinoIMU-" + String(random(0xffff), HEX);
    if (mqttClient.connect(id.c_str()))
      LOG_INFO("✅ MQTT connected (%s)", id.c_str());
    else {
      LOG_WARN("MQTT retry...");
      delay(500);
    }
  }
}

// ─── IMU sampling ───────────────────────────────────────────
void imuSamplingTask() {
  unsigned long now = micros();
  if (now < nextSampleTime) return;
  nextSampleTime += sampleIntervalUs;

  if (!imu.available()) return;
  imu.update();

  IMUData d;
  d.t = micros();
  d.ax = imu.getX();
  d.ay = imu.getY();
  d.az = imu.getZ();
  d.gx = imu.getRoll();
  d.gy = imu.getPitch();
  d.gz = imu.getYaw();

  uint16_t next = (head + 1) % BUFFER_ROWS;
  if (next == tail) tail = (tail + 1) % BUFFER_ROWS;
  buffer[head] = d;
  head = next;
}

// ─── MQTT send from buffer ──────────────────────────────────
int bufferCount() {
  uint16_t h = head, t = tail;
  return (h >= t) ? (h - t) : (BUFFER_ROWS - t + h);
}

void mqttSendingTask() {
  if (WiFi.status() != WL_CONNECTED || !mqttClient.connected()) return;
  if (bufferCount() < USER_BATCH_SIZE) return;

  int idx = 0;
  payload[idx++] = '[';
  char numbuf[16];

  for (int i = 0; i < USER_BATCH_SIZE; i++) {
    IMUData d = buffer[tail];
    tail = (tail + 1) % BUFFER_ROWS;

    payload[idx++] = '[';
    idx += sprintf(payload + idx, "%lu,", d.t);
    dtostrf(d.ax, 0, 2, numbuf); idx += sprintf(payload + idx, "%s,", numbuf);
    dtostrf(d.ay, 0, 2, numbuf); idx += sprintf(payload + idx, "%s,", numbuf);
    dtostrf(d.az, 0, 2, numbuf); idx += sprintf(payload + idx, "%s,", numbuf);
    dtostrf(d.gx, 0, 2, numbuf); idx += sprintf(payload + idx, "%s,", numbuf);
    dtostrf(d.gy, 0, 2, numbuf); idx += sprintf(payload + idx, "%s,", numbuf);
    dtostrf(d.gz, 0, 2, numbuf); idx += sprintf(payload + idx, "%s", numbuf);
    payload[idx++] = ']';
    if (i < USER_BATCH_SIZE - 1) payload[idx++] = ',';
    if (idx > (int)sizeof(payload) - 32) break;
  }

  payload[idx++] = ']';
  payload[idx] = '\0';
  mqttClient.publish(MQTT_TOPIC, payload);
}

// ─── TESTS ──────────────────────────────────────────────────
IMUData readImuOnce() {
  IMUData d;
  imu.update();
  d.t = micros();
  d.ax = imu.getX(); d.ay = imu.getY(); d.az = imu.getZ();
  d.gx = imu.getRoll(); d.gy = imu.getPitch(); d.gz = imu.getYaw();
  return d;
}

void testImuReadTime(int samples = 100) {
  LOG_INFO("🔬 Measuring IMU read time...");
  unsigned long total = 0;
  for (int i = 0; i < samples; i++) {
    unsigned long t0 = micros();
    readImuOnce();
    total += (micros() - t0);
  }
  float avg = (total / (float)samples) / 1000.0;
  LOG_INFO("✅ Average IMU read: %.3f ms", avg);
}

void testMqttSendBatchTimes() {
  LOG_INFO("📡 Measuring MQTT send time for 1–5 samples...");
  IMUData r[5];
  for (int i = 0; i < 5; i++) { r[i] = readImuOnce(); delay(40); }

  char numbuf[16];
  for (int batch = 1; batch <= 5; batch++) {
    unsigned long totalSend = 0;
    for (int iter = 0; iter < MQTT_TEST_ITER; iter++) {
      int idx = 0; payload[idx++] = '[';
      for (int j = 0; j < batch; j++) {
        IMUData &d = r[j];
        payload[idx++] = '[';
        idx += sprintf(payload + idx, "%lu,", d.t);
        dtostrf(d.ax, 0, 2, numbuf); idx += sprintf(payload + idx, "%s,", numbuf);
        dtostrf(d.ay, 0, 2, numbuf); idx += sprintf(payload + idx, "%s,", numbuf);
        dtostrf(d.az, 0, 2, numbuf); idx += sprintf(payload + idx, "%s,", numbuf);
        dtostrf(d.gx, 0, 2, numbuf); idx += sprintf(payload + idx, "%s,", numbuf);
        dtostrf(d.gy, 0, 2, numbuf); idx += sprintf(payload + idx, "%s,", numbuf);
        dtostrf(d.gz, 0, 2, numbuf); idx += sprintf(payload + idx, "%s", numbuf);
        payload[idx++] = ']';
        if (j < batch - 1) payload[idx++] = ',';
      }
      payload[idx++] = ']'; payload[idx] = '\0';

      unsigned long t0 = micros();
      mqttClient.publish(MQTT_TOPIC, payload);
      totalSend += (micros() - t0);
    }
    float avg = (totalSend / (float)MQTT_TEST_ITER) / 1000.0;
    LOG_INFO("Batch=%d | Avg MQTT send: %.3f ms", batch, avg);
  }
  LOG_INFO("✅ MQTT send test done");
}

void startThroughputTest() {
  LOG_INFO("🚀 Starting throughput benchmark...");
  const unsigned long testDuration = 5000;
  const int maxBatch = 6;
  float imuRates[maxBatch], msgRates[maxBatch];

  for (int batch = 1; batch <= maxBatch; batch++) {
    unsigned long start = millis();
    unsigned long imuCount = 0, msgCount = 0;
    while (millis() - start < testDuration) {
      readImuOnce();
      imuCount++;
      if (imuCount % batch == 0) { mqttClient.publish(MQTT_TOPIC, "[]"); msgCount++; }
    }
    float secs = (millis() - start) / 1000.0;
    imuRates[batch - 1] = imuCount / secs;
    msgRates[batch - 1] = msgCount / secs;
    LOG_INFO("Batch=%d | IMU/s=%.2f | Msg/s=%.2f", batch, imuRates[batch - 1], msgRates[batch - 1]);
  }
  LOG_INFO("✅ Throughput benchmark done");
}

// ─── Setup & Loop ───────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  while (!Serial) {}
  Modulino.begin();
  if (!imu.begin()) { LOG_ERROR("IMU not detected"); while (1) delay(1000); }

  connectWiFi();
  connectMQTT();
  nextSampleTime = micros();
  LOG_INFO("Starting Mode %d", ACTIVE_MODE);
}

void loop() {
  mqttClient.loop();

#if (ACTIVE_MODE == MODE_CONTINUOUS)
  // precise sampling + decoupled publishing
  imuSamplingTask();
  static unsigned long lastSend = 0;
  if (millis() - lastSend > MQTT_SEND_PERIOD_MS) {
    mqttSendingTask();
    lastSend = millis();
  }

#elif (ACTIVE_MODE == MODE_TEST)
  testImuReadTime(50);
  testMqttSendBatchTimes();
  startThroughputTest();
  LOG_INFO("✅ All tests complete");
  while (true) delay(1000);
#endif

  if (millis() - lastConnCheck > 5000) {
    if (WiFi.status() != WL_CONNECTED) connectWiFi();
    if (!mqttClient.connected()) connectMQTT();
    lastConnCheck = millis();
  }
}
