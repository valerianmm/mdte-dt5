#include "imu_manager.h"
#include "logger.h"

#define SAMPLING_FREQ_HZ   25

ModulinoMovement imu;
IMUData imuBuffer[IMU_BUFFER_ROWS];
uint16_t imuHead = 0, imuTail = 0;
unsigned long nextSampleTime = 0;
unsigned long sampleIntervalUs = 1000000 / SAMPLING_FREQ_HZ;

// Calibration offsets
static float axBias = 0, ayBias = 0, azBias = 0;
static float gxBias = 0, gyBias = 0, gzBias = 0;

static uint32_t msgIdCounter = 0;

bool imuInit() {
  return imu.begin();
}

void imuStartSampling() {
  nextSampleTime = micros();
}

// ─── Calibration ───────────────────────────────────────────────
void imuCalibrate(int samples) {
  LOG_INFO("🔧 Starting IMU calibration (%d samples)...", samples);
  float sumAx = 0, sumAy = 0, sumAz = 0;
  float sumGx = 0, sumGy = 0, sumGz = 0;

  for (int i = 0; i < samples; i++) {
    imu.update();
    sumAx += imu.getX();
    sumAy += imu.getY();
    sumAz += imu.getZ();
    sumGx += imu.getRoll();
    sumGy += imu.getPitch();
    sumGz += imu.getYaw();
    delay(5); // slight delay between samples
  }

  axBias = sumAx / samples;
  ayBias = sumAy / samples;
  azBias = sumAz / samples;
  gxBias = sumGx / samples;
  gyBias = sumGy / samples;
  gzBias = sumGz / samples;

  LOG_INFO("✅ Calibration done:");
  LOG_INFO("Accel bias: [%.3f, %.3f, %.3f]", axBias, ayBias, azBias);
  LOG_INFO("Gyro bias:  [%.3f, %.3f, %.3f]", gxBias, gyBias, gzBias);
}

// ─── Read Calibrated IMU Data ──────────────────────────────────
IMUData imuReadCalibrated() {
  imu.update();
  IMUData d;
  d.t = micros();
  d.ax = imu.getX() - axBias;
  d.ay = imu.getY() - ayBias;
  d.az = imu.getZ() - azBias;
  d.gx = imu.getRoll() - gxBias;
  d.gy = imu.getPitch() - gyBias;
  d.gz = imu.getYaw() - gzBias;
  return d;
}

// ─── Sampling Task ─────────────────────────────────────────────
void imuSamplingTask() {
  unsigned long now = micros();
  if (now < nextSampleTime) return;
  nextSampleTime += sampleIntervalUs;

  if (!imu.available()) return;
  imu.update();

  IMUData d;
  d.t = micros();
  d.msgId = msgIdCounter++;
  d.ax = imu.getX();
  d.ay = imu.getY();
  d.az = imu.getZ();
  d.gx = imu.getRoll();
  d.gy = imu.getPitch();
  d.gz = imu.getYaw();

  uint16_t next = (imuHead + 1) % IMU_BUFFER_ROWS;
  if (next == imuTail) imuTail = (imuTail + 1) % IMU_BUFFER_ROWS;
  imuBuffer[imuHead] = d;
  imuHead = next;
}

IMUData readImuOnce() {
  if (!imu.available()) return {};
  imu.update();

  IMUData d;
  d.t = micros();
  d.msgId = msgIdCounter++;
  d.ax = imu.getX();
  d.ay = imu.getY();
  d.az = imu.getZ();
  d.gx = imu.getRoll();
  d.gy = imu.getPitch();
  d.gz = imu.getYaw();
  return d;
}

int imuBufferCount() {
  uint16_t h = imuHead, t = imuTail;
  return (h >= t) ? (h - t) : (IMU_BUFFER_ROWS - t + h);
}
