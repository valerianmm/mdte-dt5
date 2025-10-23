#pragma once
#include "imu_manager.h"

void mqttConnect();
void mqttLoop();
void mqttPeriodicSend();
void mqttSendBuffer();
void mqttPublishSamples(IMUData *samples, int count);
