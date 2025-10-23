#include <Arduino.h>
#include "wifi_manager.h"
#include "imu_manager.h"
#include "mqtt_manager.h"
#include "tests.h"
#include "logger.h"

// ─── Modes ─────────────────────────────────────────────────
#define MODE_CONTINUOUS        1   // buffered periodic send
#define MODE_TEST              2   // benchmarking and tests
#define MODE_STREAMING         3   // fixed frequency (25Hz) streaming
#define MODE_STREAMING_FAST    4   // max-rate streaming (no delay control)

#define ACTIVE_MODE            4

// ─── Streaming configuration ────────────────────────────────
#define STREAM_FREQ_HZ     25               
#define STREAM_INTERVAL_US (1000000 / STREAM_FREQ_HZ)

// ─── Setup & Loop ───────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  while (!Serial) {}

  Modulino.begin();
  if (!imuInit()) {
    LOG_ERROR("IMU not detected");
    while (1) delay(1000);
  }

  wifiConnect();
  mqttConnect();
  imuStartSampling();

  LOG_INFO("✅ System ready — Mode %d", ACTIVE_MODE);
}

void loop() {
  mqttLoop();

#if (ACTIVE_MODE == MODE_CONTINUOUS)
  imuSamplingTask();
  mqttPeriodicSend();

#elif (ACTIVE_MODE == MODE_STREAMING)
  static unsigned long nextSampleTime = micros();

  unsigned long now = micros();
  if ((long)(now - nextSampleTime) >= 0) {
    nextSampleTime += STREAM_INTERVAL_US;

    IMUData d = readImuOnce();
    mqttPublishSamples(&d, 1);
  }

#elif (ACTIVE_MODE == MODE_STREAMING_FAST)
  IMUData d = readImuOnce();
  mqttPublishSamples(&d, 1);

#elif (ACTIVE_MODE == MODE_TEST)
  testImuReadTime(200);
  testMqttSendBatchTimes();
  testThroughput();
  testMqttSendTimingStats();
  testMqttLoopTiming();
  LOG_INFO("✅ All tests complete");
  while (true) delay(1000);
#endif
}
