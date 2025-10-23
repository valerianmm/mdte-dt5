#include "wifi_manager.h"
#include "credentials.h"
#include "logger.h"
#include <WiFiS3.h>

void wifiConnect() {
  const char *ssid = knownNetworks[0].ssid;
  const char *pass = knownNetworks[0].password;

  WiFi.disconnect();
  WiFi.begin(ssid, pass);
  unsigned long start = millis();

  while (WiFi.status() != WL_CONNECTED && millis() - start < 8000)
    delay(200);

  if (WiFi.status() == WL_CONNECTED)
    LOG_INFO("✅ Wi-Fi connected | IP: %s", WiFi.localIP().toString().c_str());
  else
    LOG_WARN("❌ Wi-Fi connection failed");
}
