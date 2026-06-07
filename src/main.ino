/*
 * Smart Watering System - Main Firmware
 * Platform: ESP32 DevKit v1
 * Author: Afreed | SR University
 * Description: Reads sensors, uploads to ThingSpeak, controls pump relay
 */

#include <WiFi.h>
#include <ThingSpeak.h>
#include "DHT.h"

// ─── WiFi & ThingSpeak Configuration ──────────────────────────
#define WIFI_SSID        "YOUR_WIFI_SSID"
#define WIFI_PASSWORD    "YOUR_WIFI_PASSWORD"
#define CHANNEL_ID       0000000          // Replace with your ThingSpeak channel ID
#define WRITE_API_KEY    "YOUR_WRITE_API_KEY"

// ─── Pin Definitions ──────────────────────────────────────────
#define SOIL_MOISTURE_PIN  34   // ADC1 channel (capacitive sensor)
#define DHT_PIN            26
#define LDR_PIN            35   // Light sensor (analog)
#define PH_PIN             33   // pH sensor analog output
#define RELAY_PIN          27   // Relay (LOW = pump ON)
#define LED_STATUS         2    // Built-in LED

// ─── Sensor Config ────────────────────────────────────────────
#define DHT_TYPE           DHT22
#define SOIL_DRY_VALUE     4095  // ADC value when completely dry
#define SOIL_WET_VALUE     1500  // ADC value when saturated
#define MOISTURE_THRESHOLD 30    // % — water plant below this
#define PUMP_ON_TIME       15000 // ms — pump run duration

// ─── Timing ───────────────────────────────────────────────────
#define UPLOAD_INTERVAL    30000  // 30 seconds between uploads
#define SENSOR_INTERVAL    5000   // 5 seconds between sensor reads

DHT dht(DHT_PIN, DHT_TYPE);
WiFiClient client;

// ─── Global State ─────────────────────────────────────────────
float soilMoisturePercent = 0;
float temperature = 0;
float humidity = 0;
float lightLevel = 0;
float phValue = 0;
bool pumpActive = false;
unsigned long lastUpload = 0;
unsigned long lastSensorRead = 0;

// ─── Setup ────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(500);

  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LED_STATUS, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH);  // Relay off (active LOW)

  dht.begin();
  connectWiFi();
  ThingSpeak.begin(client);

  Serial.println("[BOOT] Smart Watering System Initialized");
}

// ─── Main Loop ────────────────────────────────────────────────
void loop() {
  unsigned long now = millis();

  // Read sensors at interval
  if (now - lastSensorRead >= SENSOR_INTERVAL) {
    readAllSensors();
    lastSensorRead = now;
    printSensorData();
  }

  // Upload to ThingSpeak at interval
  if (now - lastUpload >= UPLOAD_INTERVAL) {
    uploadToThingSpeak();
    lastUpload = now;
  }

  // Irrigation decision
  checkIrrigationNeeded();

  // Reconnect WiFi if dropped
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WIFI] Reconnecting...");
    connectWiFi();
  }

  delay(100);
}

// ─── Sensor Functions ─────────────────────────────────────────
void readAllSensors() {
  soilMoisturePercent = readSoilMoisture();
  temperature = dht.readTemperature();
  humidity = dht.readHumidity();
  lightLevel = readLightLevel();
  phValue = readPH();

  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("[ERROR] DHT22 read failed. Retrying...");
    delay(500);
    temperature = dht.readTemperature();
    humidity = dht.readHumidity();
  }
}

float readSoilMoisture() {
  int rawADC = analogRead(SOIL_MOISTURE_PIN);
  float percent = map(rawADC, SOIL_DRY_VALUE, SOIL_WET_VALUE, 0, 100);
  return constrain(percent, 0, 100);
}

float readLightLevel() {
  int rawLDR = analogRead(LDR_PIN);
  // Convert to approximate lux (calibrate per LDR model)
  float lux = (rawLDR / 4095.0) * 1000.0;
  return lux;
}

float readPH() {
  int rawADC = analogRead(PH_PIN);
  // Typical calibration: 2.5V = pH 7.0, slope ~0.18V/pH unit
  float voltage = (rawADC / 4095.0) * 3.3;
  float ph = 7.0 + ((2.5 - voltage) / 0.18);
  return constrain(ph, 0, 14);
}

// ─── ThingSpeak Upload ────────────────────────────────────────
void uploadToThingSpeak() {
  ThingSpeak.setField(1, soilMoisturePercent);  // Field 1: Soil Moisture (%)
  ThingSpeak.setField(2, temperature);           // Field 2: Temperature (°C)
  ThingSpeak.setField(3, humidity);              // Field 3: Humidity (%)
  ThingSpeak.setField(4, lightLevel);            // Field 4: Light (lux)
  ThingSpeak.setField(5, phValue);               // Field 5: pH
  ThingSpeak.setField(6, pumpActive ? 1 : 0);   // Field 6: Pump Status

  int httpCode = ThingSpeak.writeFields(CHANNEL_ID, WRITE_API_KEY);

  if (httpCode == 200) {
    Serial.println("[THINGSPEAK] Upload successful");
    blinkLED(2);
  } else {
    Serial.printf("[THINGSPEAK] Upload failed. HTTP %d\n", httpCode);
  }
}

// ─── Irrigation Control ───────────────────────────────────────
void checkIrrigationNeeded() {
  if (!pumpActive && soilMoisturePercent < MOISTURE_THRESHOLD) {
    Serial.printf("[IRRIGATION] Soil moisture %.1f%% < threshold %d%% — WATERING\n",
                  soilMoisturePercent, MOISTURE_THRESHOLD);
    activatePump(PUMP_ON_TIME);
  }
}

void activatePump(unsigned long durationMs) {
  pumpActive = true;
  digitalWrite(RELAY_PIN, LOW);   // Activate relay (active LOW)
  digitalWrite(LED_STATUS, HIGH);
  Serial.printf("[PUMP] ON for %lu ms\n", durationMs);

  delay(durationMs);

  digitalWrite(RELAY_PIN, HIGH);  // Deactivate relay
  digitalWrite(LED_STATUS, LOW);
  pumpActive = false;
  Serial.println("[PUMP] OFF");
}

// ─── WiFi ────────────────────────────────────────────────────
void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("[WIFI] Connecting");
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\n[WIFI] Connected. IP: %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("\n[WIFI] Connection failed. Will retry.");
  }
}

// ─── Utilities ────────────────────────────────────────────────
void printSensorData() {
  Serial.println("─────────────────────────────────");
  Serial.printf("  Soil Moisture : %.1f%%\n", soilMoisturePercent);
  Serial.printf("  Temperature   : %.1f °C\n", temperature);
  Serial.printf("  Humidity      : %.1f %%\n", humidity);
  Serial.printf("  Light Level   : %.0f lux\n", lightLevel);
  Serial.printf("  pH Value      : %.2f\n", phValue);
  Serial.printf("  Pump Status   : %s\n", pumpActive ? "ON" : "OFF");
  Serial.println("─────────────────────────────────");
}

void blinkLED(int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_STATUS, HIGH);
    delay(100);
    digitalWrite(LED_STATUS, LOW);
    delay(100);
  }
}
