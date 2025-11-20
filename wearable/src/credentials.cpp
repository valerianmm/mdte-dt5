#include "credentials.h"

// Define and initialize once here
WiFiCredential knownNetworks[] = {
  // Example entry:
  // {"Valerian", "Router&Pass", "172.20.10.5"}
  {"Fredjeshuis 2: 2fred2furious", "2444666668888888", "192.168.1.251"}
};

const int numNetworks = sizeof(knownNetworks) / sizeof(knownNetworks[0]);
