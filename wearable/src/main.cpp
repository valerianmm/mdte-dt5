#include <Arduino.h>
#include <ArduinoBLE.h>

void setup() {
  Serial.begin(9600);
  while (!Serial); // Wait for Serial to be ready

  if (!BLE.begin()) {
    Serial.println("Starting BLE failed!");
    while (1);
  }

  // Set device name
  BLE.setLocalName("wearable-33");
  BLE.advertise(); // Start advertising so laptop can find it

  Serial.println("BLE device active, waiting for connections...");
}

void loop() {
  BLEDevice central = BLE.central(); // Check if a central device (laptop) is connected

  if (central) {
    Serial.print("Connected to: ");
    Serial.println(central.address());

    // While connected, print RSSI every second
    while (central.connected()) {
      int rssi = central.rssi(); // Get signal strength
      Serial.print("RSSI: ");
      Serial.print(rssi);
      Serial.println(" dBm");
      delay(1000);
    }

    Serial.println("Disconnected");
  }
}
