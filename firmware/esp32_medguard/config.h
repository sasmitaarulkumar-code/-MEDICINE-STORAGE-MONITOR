#ifndef CONFIG_H
#define CONFIG_H

// ==============================================================================
// MEDGUARD — Intelligent Medicine Storage Monitor
// ESP32 Hardware Configuration & Pin Mappings
// ==============================================================================

// Storage Unit Identification
#define STORAGE_UNIT_CODE "UNIT-A-FRIDGE"
#define FIRMWARE_VERSION  "1.0.0-PROD"

// Wi-Fi Credentials
#define WIFI_SSID         "MedGuard_IoT_Net"
#define WIFI_PASS         "MedGuardSecure2026"

// MEDGUARD Backend Server Configuration
// Change to your laptop's local IP or domain (e.g., "http://192.168.1.100:8000")
#define SERVER_HOST       "http://127.0.0.1:8000"
#define INGEST_ENDPOINT   "/api/v1/telemetry/ingest"
#define SYNC_ENDPOINT     "/api/v1/telemetry/sync"
#define DEVICE_API_KEY    "medguard-device-secret-key-2026"

// Sampling Intervals
#define SENSOR_READ_INTERVAL_MS   3000   // Read sensors every 3 seconds
#define SERVER_POST_INTERVAL_MS   5000   // Transmit telemetry to server every 5s
#define OFFLINE_RETRY_INTERVAL_MS 10000  // Attempt Wi-Fi reconnection every 10s

// ------------------------------------------------------------------------------
// Hardware Pin Mappings (ESP32 DevKit V1 30-pin)
// ------------------------------------------------------------------------------
#define PIN_DHT22         4    // GPIO 4: DHT22 / AM2302 (Temp & Humidity)
#define PIN_LDR_ADC       34   // GPIO 34 (ADC1_CH6): Photoresistor Light Sensor
#define PIN_DOOR_REED     14   // GPIO 14: Magnetic Reed Switch (Internal Pull-Up)
#define PIN_POWER_SENSE   35   // GPIO 35 (ADC1_CH7): Mains DC Voltage Divider
#define PIN_BUZZER        18   // GPIO 18: Active Piezo Buzzer
#define PIN_LED_GREEN     19   // GPIO 19: Safe Indicator
#define PIN_LED_YELLOW    21   // GPIO 21: Caution Indicator
#define PIN_LED_RED       22   // GPIO 22: High Risk / Critical Indicator

// ------------------------------------------------------------------------------
// Autonomous Local Failsafe Thresholds (Active even without internet)
// ------------------------------------------------------------------------------
#define LOCAL_MIN_TEMP_C       2.0f
#define LOCAL_MAX_TEMP_C       8.0f
#define LOCAL_MAX_HUMIDITY_RH  65.0f
#define LOCAL_LIGHT_THRESHOLD  1200   // ADC value above this indicates cabinet open
#define LOCAL_DOOR_MAX_OPEN_S  45     // Warn locally if door open > 45 seconds

// Offline Storage Limits
#define MAX_OFFLINE_RECORDS    2000   // Buffer capacity in flash / RAM

#endif // CONFIG_H
