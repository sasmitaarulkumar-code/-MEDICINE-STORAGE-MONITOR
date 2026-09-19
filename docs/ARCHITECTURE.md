# MEDGUARD System Architecture Specification

## 1. System Topology & Layers

MEDGUARD implements an asynchronous, multi-tiered IoT and Operational Intelligence architecture engineered for mission-critical healthcare cold chains.

```
+-------------------------------------------------------------------------+
|                              HARDWARE LAYER                             |
|  ESP32 Dual-Core 240MHz (FreeRTOS)                                      |
|  - Task 1 (Core 1): 3s Sensor Acquisition + Local Acoustic Failsafes    |
|  - Task 2 (Core 0): Wi-Fi State Machine + HTTP Post + Ring Buffer Sync  |
+-------------------------------------------------------------------------+
                                    │
                                    │ HTTP / JSON (Port 8000)
                                    ▼
+-------------------------------------------------------------------------+
|                              BACKEND LAYER                              |
|  FastAPI Async Micro-framework (Python 3.11)                            |
|  - Ingestion Pipeline: Validates packets, timestamps, and keys          |
|  - Offline Re-synchronizer: Replays buffered frames chronologically     |
|  - Intelligence Subsystems:                                             |
|      * 0-100 Weighted Operational Risk Engine                           |
|      * Ordinary Least Squares Linear Trend Forecaster                   |
|      * Rolling Window Z-Score Anomaly Detector                          |
|  - Alert State Machine: Level 1 (Warning), L2 (High Risk), L3 (Critical)|
|  - Persistence: SQLite with Write-Ahead Logging (WAL mode)              |
|  - Event Dispatcher: WebSocket connection pool manager                  |
+-------------------------------------------------------------------------+
                                    │
                                    │ WebSockets (Full Duplex) + REST
                                    ▼
+-------------------------------------------------------------------------+
|                             FRONTEND LAYER                              |
|  Operational Healthcare Dashboard (HTML5, Tailwind, Chart.js, Recharts) |
|  - Multi-Storage Switcher (Pharmacy Fridge, Vaccine Freezer, Ambient)   |
|  - Dynamic Risk Gauge & Threshold Boundary Charts                       |
|  - Medicine Impact Inspector (Batch #, Quantities, Expiry, SOPs)        |
|  - Regulatory Compliance & Audit Trail Center                           |
|  - Interactive 3-Minute Hackathon Demo Mode Controller                  |
+-------------------------------------------------------------------------+
```

---

## 2. Failure Handling & Resilient Design Patterns

### A. Wi-Fi Disconnect & Network Drops (Offline-First Design)
- **Local Ring Buffer**: When Wi-Fi is lost, the ESP32 buffers readings to flash storage (`LittleFS`) or static RAM ring buffer (capacity: 2,000 readings).
- **Autonomous Local Alarms**: Core 1 evaluates local temperature and door limits directly on the MCU. If limits are violated while offline, the local active buzzer and RGB LED sound immediately without waiting for server connectivity.
- **Reconnection & Catch-Up Sync**: Upon Wi-Fi reconnection, buffered frames are dispatched via `POST /api/v1/telemetry/sync` in batched chunks of 30. The backend marks these with `is_offline_sync: true` and reconstructs the audit timeline seamlessly.

### B. Sensor Probe Malfunction or Disconnection
- If the DHT22 or temperature probe is unplugged, the firmware catches `isnan()` and sets an error flag.
- The backend's `AnomalyDetector` catches out-of-range sensor readings (e.g. -999°C or >100°C) and generates an `ANOMALY_SPIKE` / `SENSOR_FAULT` alert, preventing corrupt data from poisoning the rolling baseline.

### C. Power Failure
- The power sense voltage divider on GPIO 35 trips immediately when AC mains drop.
- The backend flags `POWER INTERRUPTION DETECTED`, starts the elapsed power failure timer, and raises the Risk Score to Critical tier (81–100).
- If power is restored, the alert auto-resolves and logs the exact blackout duration into the audit trail.

---

## 3. Concurrency & High-Throughput Strategy
- **SQLite WAL Mode**: Enabling `PRAGMA journal_mode=WAL` and `PRAGMA synchronous=NORMAL` allows concurrent read queries from multiple dashboard clients without blocking background telemetry writes.
- **Asynchronous WebSockets**: Updates are broadcast non-blockingly to all open browser sessions in <10ms.
