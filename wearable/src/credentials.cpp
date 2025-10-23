#include "credentials.h"

// Define and initialize once here
WiFiCredential knownNetworks[] = {
  // Example entry:
  {"Valerian", "Router&Pass", "172.20.10.5"}
};

const int numNetworks = sizeof(knownNetworks) / sizeof(knownNetworks[0]);
