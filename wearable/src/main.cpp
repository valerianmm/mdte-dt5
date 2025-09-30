#include <Wire.h>
#include "Modulino.h"

ModulinoMovement movement;  // IMU instance

void setup() {
  // Start Serial Monitor
  Serial.begin(115200);
  while (!Serial);

  // Initialize I2C bus
  Modulino.begin();

  // Initialize IMU sensor
  if (!movement.begin()) {
    Serial.println("IMU initialization failed!");
    while (1);  // Stop here if IMU not found
  }
  Serial.println("IMU initialized successfully.");
}

void loop() {
  // Check if new data is available
  if (movement.available()) {
    movement.update(); // Read fresh data

    // Get acceleration (m/s²)
    float ax = movement.getX();
    float ay = movement.getY();
    float az = movement.getZ();

    // Get gyroscope data (dps - degrees per second)
    float gx = movement.getRoll();
    float gy = movement.getPitch();
    float gz = movement.getYaw();

    // Print data
    Serial.print("Accel (m/s²): X=");
    Serial.print(ax);
    Serial.print(" Y=");
    Serial.print(ay);
    Serial.print(" Z=");
    Serial.print(az);

    Serial.print(" | Gyro (dps): Roll=");
    Serial.print(gx);
    Serial.print(" Pitch=");
    Serial.print(gy);
    Serial.print(" Yaw=");
    Serial.println(gz);
  }

  delay(100); // Small delay to avoid flooding Serial
}
