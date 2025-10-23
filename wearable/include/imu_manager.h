#pragma once
#include <Arduino.h>
#include "Modulino.h"

struct IMUData {
  unsigned long t;
  float ax, ay, az;
  float gx, gy, gz;
};

bool imuInit();
void imuStartSampling();
void imuSamplingTask();
IMUData readImuOnce();
int imuBufferCount();
extern IMUData imuBuffer[];
extern uint16_t imuHead, imuTail;
