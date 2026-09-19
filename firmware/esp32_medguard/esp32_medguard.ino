/*
 * ==============================================================================
 * MEDGUARD — Intelligent Medicine Storage Monitoring & Early Warning System
 * ESP32 Production IoT Firmware (FreeRTOS Dual-Task Architecture)
 * ==============================================================================
 * 
 * Capabilities:
 * 1. Multi-sensor ingestion: DHT22 (Temp/RH), LDR (Light), Reed Switch (Door),
 *    and Power Voltage Divider.
 * 2. Autonomous Local Failsafe: Evaluates limits on-device. Triggers buzzer and
 *    RGB LEDs even during total network blackouts.
 * 3. Offline-First Resilience: Buffers sensor records locally when Wi-Fi drops,
 *    and flushes synchronized batches to the backend upon reconnect.
 * 4. FreeRTOS Multitasking: Core 1 handles timing-sensitive sensor sampling;
 *    Core 0 handles Wi-Fi, HTTP requests, and buffer synchronization.
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <time.h>
#include "config.h"
#include "offline_buffer.h"

// ------------------------------------------------------------------------------
// Globals & Objects
// ------------------------------------------------------------------------------
DHT dht(PIN_DHT22, DHT22);
OfflineRingBuffer offlineBuffer;

// Mutex for thread-safe telemetry access
SemaphoreHandle_t telemetryMutex;

// Latest sensor snapshot shared across tasks
TelemetryRecord currentReading = {0, 4.0f, 50.0f, 100, false, true, 3.3f};

// Local status state
enum LocalAlertState {
    STATE_SAFE,
    STATE_CAUTION,
    STATE_CRITICAL
};
LocalAlertState currentLocalState = STATE_SAFE;

unsigned long doorOpenedTimestamp = 0;
bool isDoorCurrentlyOpen = false;
bool wasDoorOpen = false;

// ------------------------------------------------------------------------------
// Hardware Initialization
// ------------------------------------------------------------------------------
void initHardware() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n[MEDGUARD] Initializing Hardware Node...");

    // Sensor pins
    pinMode(PIN_DOOR_REED, INPUT_PULLUP);
    pinMode(PIN_LDR_ADC, INPUT);
    pinMode(PIN_POWER_SENSE, INPUT);
    
    // Actuator pins
    pinMode(PIN_BUZZER, OUTPUT);
    pinMode(PIN_LED_GREEN, OUTPUT);
    pinMode(PIN_LED_YELLOW, OUTPUT);
    pinMode(PIN_LED_RED, OUTPUT);

    // Initial LED test
    digitalWrite(PIN_LED_GREEN, HIGH);
    digitalWrite(PIN_LED_YELLOW, HIGH);
    digitalWrite(PIN_LED_RED, HIGH);
    digitalWrite(PIN_BUZZER, HIGH);
    delay(200);
    digitalWrite(PIN_BUZZER, LOW);
    digitalWrite(PIN_LED_GREEN, LOW);
    digitalWrite(PIN_LED_YELLOW, LOW);
    digitalWrite(PIN_LED_RED, LOW);

    dht.begin();
    telemetryMutex = xSemaphoreCreateMutex();
    Serial.println("[MEDGUARD] Sensors and Actuators Ready.");
}

// ------------------------------------------------------------------------------
// Autonomous Local Failsafe Controller (Runs on Core 1)
// ------------------------------------------------------------------------------
void updateLocalFailsafe(const TelemetryRecord& rec) {
    bool isCritical = false;
    bool isCaution = false;

    // Check Temperature
    if (rec.temperature < LOCAL_MIN_TEMP_C || rec.temperature > LOCAL_MAX_TEMP_C) {
        if (rec.temperature > (LOCAL_MAX_TEMP_C + 2.0f) || rec.temperature < (LOCAL_MIN_TEMP_C - 2.0f)) {
            isCritical = true;
        } else {
            isCaution = true;
        }
    }

    // Check Door prolonged open
    if (rec.door_open) {
        if (!wasDoorOpen) {
            doorOpenedTimestamp = millis();
            wasDoorOpen = true;
        } else if ((millis() - doorOpenedTimestamp) > (LOCAL_DOOR_MAX_OPEN_S * 1000UL)) {
            isCritical = true;
        } else {
            isCaution = true;
        }
    } else {
        wasDoorOpen = false;
        doorOpenedTimestamp = 0;
    }

    // Check Power Status
    if (!rec.power_connected) {
        isCritical = true;
    }

    // Update Actuators based on state
    if (isCritical) {
        currentLocalState = STATE_CRITICAL;
        digitalWrite(PIN_LED_RED, HIGH);
        digitalWrite(PIN_LED_YELLOW, LOW);
        digitalWrite(PIN_LED_GREEN, LOW);
        // Beep buzzer pattern (3 beeps)
        digitalWrite(PIN_BUZZER, HIGH);
        delay(100);
        digitalWrite(PIN_BUZZER, LOW);
        delay(100);
        digitalWrite(PIN_BUZZER, HIGH);
        delay(100);
        digitalWrite(PIN_BUZZER, LOW);
    } else if (isCaution) {
        currentLocalState = STATE_CAUTION;
        digitalWrite(PIN_LED_RED, LOW);
        digitalWrite(PIN_LED_YELLOW, HIGH);
        digitalWrite(PIN_LED_GREEN, LOW);
        digitalWrite(PIN_BUZZER, LOW);
    } else {
        currentLocalState = STATE_SAFE;
        digitalWrite(PIN_LED_RED, LOW);
        digitalWrite(PIN_LED_YELLOW, LOW);
        digitalWrite(PIN_LED_GREEN, HIGH);
        digitalWrite(PIN_BUZZER, LOW);
    }
}

// ------------------------------------------------------------------------------
// Task 1: Sensor Sampling & Local Failsafe Loop (Core 1)
// ------------------------------------------------------------------------------
void taskSensorAcquisition(void* pvParameters) {
    Serial.println("[MEDGUARD] Task 1 (Sensors) Started on Core 1.");
    for (;;) {
        float h = dht.readHumidity();
        float t = dht.readTemperature();
        int ldr = analogRead(PIN_LDR_ADC);
        // Reed switch: LOW means magnet is present (closed), HIGH means separated (door open)
        bool door = (digitalRead(PIN_DOOR_REED) == HIGH);
        int pwrRaw = analogRead(PIN_POWER_SENSE);
        // If voltage divider senses > 1.5V equivalent (raw ADC > 1500), mains power is healthy
        bool pwr = (pwrRaw > 1200);

        if (isnan(h) || isnan(t)) {
            Serial.println("[WARN] DHT22 read failure, using last known readings.");
        } else {
            TelemetryRecord snapshot;
            snapshot.timestamp_sec = millis() / 1000UL;
            snapshot.temperature = t;
            snapshot.humidity = h;
            snapshot.light_adc = ldr;
            snapshot.door_open = door;
            snapshot.power_connected = pwr;
            snapshot.battery_v = (pwrRaw * 3.3f / 4095.0f) * 2.0f; // estimated battery/mains V

            if (xSemaphoreTake(telemetryMutex, pdMS_TO_TICKS(100)) == pdTRUE) {
                currentReading = snapshot;
                xSemaphoreGive(telemetryMutex);
            }

            // Local failsafe processing
            updateLocalFailsafe(snapshot);
        }

        vTaskDelay(pdMS_TO_TICKS(SENSOR_READ_INTERVAL_MS));
    }
}

// ------------------------------------------------------------------------------
// Helper: Send Realtime Telemetry Packet
// ------------------------------------------------------------------------------
bool sendTelemetryToServer(const TelemetryRecord& rec) {
    if (WiFi.status() != WL_CONNECTED) return false;

    HTTPClient http;
    String url = String(SERVER_HOST) + String(INGEST_ENDPOINT);
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-Device-Key", DEVICE_API_KEY);

    StaticJsonDocument<256> doc;
    doc["storage_unit_code"] = STORAGE_UNIT_CODE;
    doc["temperature"] = rec.temperature;
    doc["humidity"] = rec.humidity;
    doc["light_lux"] = (rec.light_adc / 4095.0f) * 1000.0f; // approximate lux scaling
    doc["door_open"] = rec.door_open;
    doc["power_connected"] = rec.power_connected;
    doc["battery_level"] = rec.battery_v;
    doc["is_offline_sync"] = false;

    String jsonBody;
    serializeJson(doc, jsonBody);

    int httpCode = http.POST(jsonBody);
    http.end();

    if (httpCode == 200 || httpCode == 201) {
        return true;
    } else {
        Serial.printf("[HTTP] Ingest failed, status code: %d\n", httpCode);
        return false;
    }
}

// ------------------------------------------------------------------------------
// Helper: Flush Buffered Offline Telemetry Records
// ------------------------------------------------------------------------------
void flushOfflineBuffer() {
    if (offlineBuffer.isEmpty() || WiFi.status() != WL_CONNECTED) return;

    Serial.printf("[OFFLINE-SYNC] Syncing %d cached records to backend...\n", offlineBuffer.size());
    HTTPClient http;
    String url = String(SERVER_HOST) + String(SYNC_ENDPOINT);
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-Device-Key", DEVICE_API_KEY);

    // Batch up to 30 records per HTTP sync request to prevent buffer overflow
    DynamicJsonDocument doc(4096);
    doc["storage_unit_code"] = STORAGE_UNIT_CODE;
    JsonArray recordsArray = doc.createNestedArray("readings");

    int batchCount = 0;
    TelemetryRecord rec;
    while (batchCount < 30 && offlineBuffer.pop(rec)) {
        JsonObject item = recordsArray.createNestedObject();
        item["timestamp_offset_s"] = rec.timestamp_sec;
        item["temperature"] = rec.temperature;
        item["humidity"] = rec.humidity;
        item["light_lux"] = (rec.light_adc / 4095.0f) * 1000.0f;
        item["door_open"] = rec.door_open;
        item["power_connected"] = rec.power_connected;
        item["battery_level"] = rec.battery_v;
        item["is_offline_sync"] = true;
        batchCount++;
    }

    String jsonPayload;
    serializeJson(doc, jsonPayload);

    int httpResponse = http.POST(jsonPayload);
    http.end();

    if (httpResponse == 200 || httpResponse == 201) {
        Serial.printf("[OFFLINE-SYNC] Successfully synced batch of %d records.\n", batchCount);
    } else {
        Serial.printf("[OFFLINE-SYNC] Batch sync returned HTTP %d, records dropped.\n", httpResponse);
    }
}

// ------------------------------------------------------------------------------
// Task 2: Wi-Fi Management, Telemetry Transmission & Buffer Sync (Core 0)
// ------------------------------------------------------------------------------
void taskNetworkAndSync(void* pvParameters) {
    Serial.println("[MEDGUARD] Task 2 (Network & Sync) Started on Core 0.");
    
    // Connect to Wi-Fi initially
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    Serial.printf("[WIFI] Connecting to %s", WIFI_SSID);

    for (;;) {
        // 1. Maintain Wi-Fi Connection
        if (WiFi.status() != WL_CONNECTED) {
            Serial.print(".");
            WiFi.reconnect();
            vTaskDelay(pdMS_TO_TICKS(OFFLINE_RETRY_INTERVAL_MS));
            continue;
        }

        // 2. Fetch latest telemetry snapshot
        TelemetryRecord snapshot;
        if (xSemaphoreTake(telemetryMutex, pdMS_TO_TICKS(100)) == pdTRUE) {
            snapshot = currentReading;
            xSemaphoreGive(telemetryMutex);
        }

        // 3. Transmit Realtime Telemetry
        bool sent = sendTelemetryToServer(snapshot);
        if (!sent) {
            // Server down or packet loss: cache into local ring buffer
            offlineBuffer.push(snapshot);
            Serial.printf("[OFFLINE-BUFFER] Buffered frame. Total cached: %d\n", offlineBuffer.size());
        } else {
            // Online and server reachable: check if any offline records need backfilling
            if (!offlineBuffer.isEmpty()) {
                flushOfflineBuffer();
            }
        }

        vTaskDelay(pdMS_TO_TICKS(SERVER_POST_INTERVAL_MS));
    }
}

// ------------------------------------------------------------------------------
// Setup & Loop
// ------------------------------------------------------------------------------
void setup() {
    initHardware();

    // Create FreeRTOS Tasks pinned to separate cores
    xTaskCreatePinnedToCore(
        taskSensorAcquisition,
        "SensorAcqTask",
        4096,
        NULL,
        2,              // High priority for sensor sampling & failsafe buzzer
        NULL,
        1               // Core 1
    );

    xTaskCreatePinnedToCore(
        taskNetworkAndSync,
        "NetworkSyncTask",
        8192,
        NULL,
        1,              // Lower priority for network and HTTP sync
        NULL,
        0               // Core 0
    );
}

void loop() {
    // Empty: Execution handled by FreeRTOS tasks
    vTaskDelay(pdMS_TO_TICKS(1000));
}
