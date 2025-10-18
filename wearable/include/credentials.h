#ifndef CREDENTIALS_H
#define CREDENTIALS_H

struct WiFiCredential {
  const char* ssid;
  const char* password;
  const char* mqtt_host; 
};

WiFiCredential knownNetworks[] = {
  {"Fredjeshuis 2: 2fred2furious", "2444666668888888", "Valerians-MacBook-Pro.local"},
  // {"Valerian", "Router&Pass","172.20.10.5"},
};

const int numNetworks = sizeof(knownNetworks) / sizeof(knownNetworks[0]);

#endif // CREDENTIALS_H
