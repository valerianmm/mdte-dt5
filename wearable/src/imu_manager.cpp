#include "imu_manager.h"
#include "logger.h"

#define BUFFER_ROWS        500
#define SAMPLING_FREQ_HZ   25

ModulinoMovement imu;
IMUData imuBuffer[BUFFER_ROWS];
uint16_t imuHead = 0, imuTail = 0;
unsigned long nextSampleTime = 0;
unsigned long sampleIntervalUs = 1000000 / SAMPLING_FREQ_HZ;

bool imuInit() {
  return imu.begin();
}

void imuStartSampling() {
  nextSampleTime = micros();
}

void imuSamplingTask() {
  unsigned long now = micros();
  if (now < nextSampleTime) return;
  nextSampleTime += sampleIntervalUs;

  if (!imu.available()) return;
  imu.update();

  IMUData d;
  d.t = micros();
  d.ax = imu.getX();  d.ay = imu.getY();  d.az = imu.getZ();
  d.gx = imu.getRoll(); d.gy = imu.getPitch(); d.gz = imu.getYaw();

  uint16_t next = (imuHead + 1) % BUFFER_ROWS;
  if (next == imuTail) imuTail = (imuTail + 1) % BUFFER_ROWS;
  imuBuffer[imuHead] = d;
  imuHead = next;
}

IMUData readImuOnce() {
  IMUData d;
  imu.update();
  d.t = micros();
  d.ax = imu.getX(); d.ay = imu.getY(); d.az = imu.getZ();
  d.gx = imu.getRoll(); d.gy = imu.getPitch(); d.gz = imu.getYaw();
  return d;
}

int imuBufferCount() {
  uint16_t h = imuHead, t = imuTail;
  return (h >= t) ? (h - t) : (BUFFER_ROWS - t + h);
}
