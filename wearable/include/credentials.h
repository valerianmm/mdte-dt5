#ifndef CREDENTIALS_H
#define CREDENTIALS_H

struct WiFiCredential {
  const char* ssid;
  const char* password;
  const char* mqtt_host;
};

// Declaration only — no array initialization here
extern WiFiCredential knownNetworks[];
extern const int numNetworks;

#endif
