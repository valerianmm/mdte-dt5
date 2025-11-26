#include <Arduino.h>
#include "wifi_manager.h"
#include "imu_manager.h"
#include "mqtt_manager.h"
#include "tests.h"
#include "logger.h"

// ─── Modes ─────────────────────────────────────────────────
#define MODE_CONTINUOUS                 1 // buffered periodic send
#define MODE_TEST                       2 // benchmarking and tests
#define MODE_STREAMING                  3 // fixed frequency (25Hz) streaming
#define MODE_STR4MING_FAST              4 // max-rate streaming (no delay control)
#define MODE_TEST_NO_CALIBRATION        5 // TC-01 test sampling before calibration
#define MODE_TEST_WITH_CALIBRATION      6 // TC-01 test sampling after calibration
#define MODE_TEST_SAMPLE_IMU            7 // TC-02
#define MODE_TEST_TEST_WIFI             8 // TC-03
#define MODE_TEST_TEST_MQTT             9 // TC-04


#define MODE                           1

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

#if (MODE != MODE_TEST_NO_CALIBRATION)
  LOG_INFO("🪩 Place IMU flat and still for calibration...");
  delay(2000);
  imuCalibrate(200);  // calibrate before starting
#endif

  wifiConnect();
  mqttConnect();
  imuStartSampling();

  LOG_INFO("✅ System ready — Mode %d", MODE);
}


void loop() {
  mqttLoop();

#if (MODE == MODE_CONTINUOUS)
  imuSamplingTask();
  mqttPeriodicSend();

#elif (MODE == MODE_STREAMING)
  static unsigned long nextSampleTime = micros();

  unsigned long now = micros();
  if ((long)(now - nextSampleTime) >= 0) {
    nextSampleTime += STREAM_INTERVAL_US;

    IMUData d = readImuOnce();
    mqttPublishSamples(&d, 1);
  }

#elif (MODE == MODE_STREAMING_FAST)
  IMUData d = readImuOnce();
  mqttPublishSamples(&d, 1);

#elif (MODE == MODE_TEST)
  testImuReadTime(200);
  testMqttSendBatchTimes();
  testThroughput();
  testMqttSendTimingStats();
  testMqttLoopTiming();
  LOG_INFO("✅ All tests complete");
  while (true) delay(1000);


#elif (MODE == MODE_TEST_NO_CALIBRATION)  
  IMUData d = readImuOnce();
  mqttPublishSamples(&d, 1);

#elif (MODE == MODE_TEST_WITH_CALIBRATION)  
  IMUData d = readImuOnce();
  mqttPublishSamples(&d, 1);


#elif (MODE == MODE_TEST_SAMPLE_IMU)  
  IMUData d = readImuOnce();
  LOG_INFO("IMU Data | id=%lu | t=%lu | ax=%.3f ay=%.3f az=%.3f | gx=%.3f gy=%.3f gz=%.3f",
           (unsigned long)d.msgId, d.t, d.ax, d.ay, d.az, d.gx, d.gy, d.gz);
  delay(100);

#elif (MODE == MODE_TEST_TEST_WIFI)  
  delay(1000);

#elif (MODE == MODE_TEST_TEST_MQTT)  
  IMUData d = readImuOnce();
  mqttPublishSamples(&d, 1);

// #elif (MODE == MODE_TEST_PACKET_DELIVERY_RATE)  
//   IMUData d = readImuOnce();
//   mqttPublishSamples(&d, 1);

#endif
}
