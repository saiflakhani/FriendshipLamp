#include <WiFi.h>
#include <HTTPClient.h>

const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";

// Replace with your flask server IP or Domain Name
const char* SERVER_BASE_URL = "http://friendshiplamp.lakhanimediaserver.xyz";

// Lamp Configuration
const char* LAMP_NAME = "Saif's Lamp"; // The name that will appear on the website
const int BLINK_TIMES = 3;             // How many times it blinks when a message arrives

const int LED_PIN = 2; // Onboard LED on most ESP32 Dev Boards. Use an external LED with resistor if desired.
const int SLEEP_MINUTES = 3;

// RTC Data for fast boot (persists across deep sleep to bypass long DHCP setup!)
RTC_DATA_ATTR int rtc_valid = 0;
RTC_DATA_ATTR uint8_t rtc_bssid[6];
RTC_DATA_ATTR int rtc_channel;

String getMacAddress() {
  String mac = WiFi.macAddress();
  mac.replace(":", "");
  return mac;
}

void goToSleep() {
  Serial.println("Going to sleep now...\n=================");
  delay(10); 
  // No need to wire D0 to RST on ESP32! The internal RTC timer wakes the core up.
  esp_sleep_enable_timer_wakeup(SLEEP_MINUTES * 60 * 1000000ULL);
  esp_deep_sleep_start();
  // Anything below this never executes. Deep sleep restarts execution from setup() on wake up.
}

void connectToWiFiFast() {
  WiFi.mode(WIFI_STA);
  
  if (rtc_valid == 1) {
    Serial.println("Attempting fast connect using RTC info...");
    WiFi.begin(WIFI_SSID, WIFI_PASS, rtc_channel, rtc_bssid);
  } else {
    Serial.println("No RTC info, normal DHCP connect...");
    WiFi.begin(WIFI_SSID, WIFI_PASS);
  }

  int retries = 0;
  // Wait up to 5 seconds for fast connect
  while (WiFi.status() != WL_CONNECTED && retries < 100) { 
    delay(50);
    retries++;
  }

  // Fallback if fast connect failed
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Fast connect failed. Falling back to normal DHCP...");
    WiFi.disconnect();
    delay(100);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    
    retries = 0;
    while (WiFi.status() != WL_CONNECTED && retries < 20) {
      delay(500);
      Serial.print(".");
      retries++;
    }
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected.");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    
    // Save successful parameters for next boot
    rtc_valid = 1;
    rtc_channel = WiFi.channel();
    uint8_t* bssid = WiFi.BSSID();
    for(int i=0; i<6; i++) {
        rtc_bssid[i] = bssid[i];
    }
  } else {
    Serial.println("\nFailed to connect entirely. Going back to sleep.");
    goToSleep();
  }
}

void blinkLED(int times) {
  for (int i=0; i<times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(500);
    digitalWrite(LED_PIN, LOW);
    delay(500);
  }
}

void setup() {
  btStop(); // Turn off Bluetooth radio to save battery
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW); // Turn off internal LED

  Serial.println("\n\n=== ESP32 Waking up from Deep Sleep ===");

  unsigned long startTime = millis();
  connectToWiFiFast();
  Serial.printf("WiFi connected in %lu ms\n", millis() - startTime);

  String lampId = getMacAddress();

  HTTPClient http;
  String statusUrl = String(SERVER_BASE_URL) + "/api/lamp/status?id=" + lampId + "&name=" + String(LAMP_NAME);
  String ackUrl = String(SERVER_BASE_URL) + "/api/lamp/ack?id=" + lampId;

  Serial.println("[HTTP] Checking server: " + statusUrl);
  
  if (http.begin(statusUrl)) {
    http.setTimeout(3000); // Fail fast
    int httpCode = http.GET();
    
    if (httpCode > 0) {
      if (httpCode == HTTP_CODE_OK) {
        String payload = http.getString();
        
        if (payload.indexOf("\"active\": true") > 0 || payload.indexOf("\"active\":true") > 0) {
          Serial.println("Friend is thinking of you! Blinking LED...");
          
          blinkLED(BLINK_TIMES);
          
          HTTPClient ackHttp;
          if (ackHttp.begin(ackUrl)) {
            ackHttp.POST("");
            ackHttp.end();
          }
        } else {
          Serial.println("No new message. Lamp is inactive.");
        }
      }
    } else {
      Serial.printf("[HTTP] GET... failed, error: %s\n", http.errorToString(httpCode).c_str());
    }
    http.end();
  }

  goToSleep();
}

void loop() {
  // Empty. Deep sleep reboots the chip
}
