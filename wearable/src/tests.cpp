#include "tests.h"
#include "imu_manager.h"
#include "mqtt_manager.h"
#include "logger.h"
#include <algorithm>
#include <vector>

#define MQTT_TEST_ITER 50

void testImuReadTime(int samples) {
  LOG_INFO("🔬 Measuring IMU read time...");
  unsigned long total = 0;
  for (int i = 0; i < samples; i++) {
    unsigned long t0 = micros();
    readImuOnce();
    total += micros() - t0;
  }
  LOG_INFO("✅ Avg IMU read: %.3f ms", (total / (float)samples) / 1000.0);
}

void testMqttSendBatchTimes() {
  LOG_INFO("📡 Measuring MQTT send time for 1–5 samples...");
  IMUData samples[5];
  for (int i = 0; i < 5; i++) samples[i] = readImuOnce();

  for (int batch = 1; batch <= 5; batch++) {
    unsigned long total = 0;
    for (int iter = 0; iter < MQTT_TEST_ITER; iter++) {
      unsigned long t0 = micros();
      mqttPublishSamples(samples, batch);
      total += micros() - t0;
    }
    LOG_INFO("Batch=%d | Avg send: %.3f ms",
             batch, (total / (float)MQTT_TEST_ITER) / 1000.0);
  }
}

void testThroughput() {
  LOG_INFO("🚀 Throughput benchmark...");
  const unsigned long testDuration = 5000;
  const int maxBatch = 6;
  float imuRates[maxBatch], msgRates[maxBatch];

  for (int batch = 1; batch <= maxBatch; batch++) {
    unsigned long start = millis(), imuCount = 0, msgCount = 0;
    while (millis() - start < testDuration) {
      readImuOnce();
      imuCount++;
      if (imuCount % batch == 0) {
        mqttPublishSamples(nullptr, 0);
        msgCount++;
      }
    }
    float secs = (millis() - start) / 1000.0;
    imuRates[batch - 1] = imuCount / secs;
    msgRates[batch - 1] = msgCount / secs;
    LOG_INFO("Batch=%d | IMU/s=%.2f | Msg/s=%.2f",
             batch, imuRates[batch - 1], msgRates[batch - 1]);
  }
}

void testMqttSendTimingStats() {
  LOG_INFO("📊 Starting MQTT send timing benchmark...");

  IMUData sample = readImuOnce();  // one reading reused for all
  const int numTests = 100;
  const int maxBatch = 5;

  for (int batch = 1; batch <= maxBatch; batch++) {
    std::vector<float> times;
    times.reserve(numTests);

    IMUData samples[5];
    for (int i = 0; i < batch; i++) samples[i] = sample;

    for (int i = 0; i < numTests; i++) {
      unsigned long t0 = micros();

      mqttPublishSamples(samples, batch);
      mqttLoop();  // keep connection alive

      unsigned long elapsedUs = micros() - t0;
      times.push_back(elapsedUs / 1000.0f); // ms
    }

    // Compute stats
    auto minmax = std::minmax_element(times.begin(), times.end());
    float sum = 0;
    for (float v : times) sum += v;
    float mean = sum / numTests;

    std::vector<float> sorted = times;
    std::sort(sorted.begin(), sorted.end());
    float median = (sorted[numTests / 2] + sorted[(numTests - 1) / 2]) / 2.0f;

    // Compute mode (most frequent value rounded to nearest ms)
    const int modeBins = 200; // covers 0–199 ms typical range
    int counts[modeBins] = {0};
    for (float v : times) {
      int bin = (int)(v + 0.5f);
      if (bin >= 0 && bin < modeBins) counts[bin]++;
    }
    int modeVal = 0, modeCount = 0;
    for (int i = 0; i < modeBins; i++) {
      if (counts[i] > modeCount) { modeCount = counts[i]; modeVal = i; }
    }

    LOG_INFO(
      "Batch=%d | min=%.3f ms | max=%.3f ms | mean=%.3f ms | median=%.3f ms | mode=%d ms",
      batch, *minmax.first, *minmax.second, mean, median, modeVal
    );
  }

  LOG_INFO("✅ MQTT timing benchmark complete.");
}

void testMqttLoopTiming() {
  LOG_INFO("🧩 Starting mqttLoop() timing benchmark...");

  const int numTests = 1000;
  std::vector<float> times;
  times.reserve(numTests);

  for (int i = 0; i < numTests; i++) {
    unsigned long t0 = micros();
    mqttLoop();
    unsigned long elapsedUs = micros() - t0;
    times.push_back(elapsedUs / 1000.0f);  // ms
  }

  // Compute statistics
  auto minmax = std::minmax_element(times.begin(), times.end());
  float sum = 0;
  for (float v : times) sum += v;
  float mean = sum / numTests;

  std::vector<float> sorted = times;
  std::sort(sorted.begin(), sorted.end());
  float median = (sorted[numTests / 2] + sorted[(numTests - 1) / 2]) / 2.0f;

  // Compute mode (rounded ms bins)
  const int modeBins = 50;  // good for 0–50 ms
  int counts[modeBins] = {0};
  for (float v : times) {
    int bin = (int)(v + 0.5f);
    if (bin >= 0 && bin < modeBins) counts[bin]++;
  }
  int modeVal = 0, modeCount = 0;
  for (int i = 0; i < modeBins; i++) {
    if (counts[i] > modeCount) { modeCount = counts[i]; modeVal = i; }
  }

  LOG_INFO("✅ mqttLoop() timing results (over %d iterations):", numTests);
  LOG_INFO("Min=%.3f ms | Max=%.3f ms | Mean=%.3f ms | Median=%.3f ms | Mode=%d ms",
           *minmax.first, *minmax.second, mean, median, modeVal);
}
