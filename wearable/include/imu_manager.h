#pragma once
#include <Arduino.h>
#include "Modulino.h"

// Buffer size (reduced to fit RAM of the target board)
constexpr size_t IMU_BUFFER_ROWS = 200;

struct IMUData {
  unsigned long t;
  uint32_t msgId;
  float ax, ay, az;
  float gx, gy, gz;
};

bool imuInit();
void imuStartSampling();
void imuSamplingTask();
IMUData readImuOnce();
int imuBufferCount();

// New calibration functions
void imuCalibrate(int samples = 200);
IMUData imuReadCalibrated();

extern IMUData imuBuffer[IMU_BUFFER_ROWS];
extern uint16_t imuHead, imuTail;
