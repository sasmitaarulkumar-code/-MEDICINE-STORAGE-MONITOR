# MEDGUARD API Reference Specification

Base URL: `http://127.0.0.1:8000/api/v1`

---

## 1. Authentication Endpoints

### `POST /auth/login`
Authenticates a user and returns a JWT access token.
- **Form Data**: `username`, `password`
- **Response `200 OK`**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "role": "admin",
  "username": "admin",
  "full_name": "Dr. Eleanor Vance (Chief Pharmacist)"
}
```

### `GET /auth/me`
Returns current authenticated user details.
- **Headers**: `Authorization: Bearer <TOKEN>`

---

## 2. Storage Units Endpoints

### `GET /storage-units`
Lists all monitored storage units along with their latest telemetry readings, active alert counts, medicine inventory counts, risk score, and operational status.
- **Response `200 OK`**:
```json
[
  {
    "id": 1,
    "unit_code": "UNIT-A-FRIDGE",
    "name": "Pharmacy Refrigerator A",
    "unit_type": "refrigerator",
    "location": "Room 102 - Outpatient Pharmacy",
    "default_min_temp": 2.0,
    "default_max_temp": 8.0,
    "default_min_humidity": 30.0,
    "default_max_humidity": 65.0,
    "power_status": true,
    "status": "SAFE",
    "current_risk_score": 12.5,
    "door_open_state": false,
    "latest_temperature": 4.2,
    "latest_humidity": 48.0,
    "latest_light_lux": 12.0,
    "active_alert_count": 0,
    "medicine_count": 4
  }
]
```

### `PUT /storage-units/{id}`
Updates the configured temperature and humidity threshold boundaries for a storage unit.

---

## 3. Telemetry Ingestion Endpoints

### `POST /telemetry/ingest`
Primary real-time sensor packet ingestion endpoint called by ESP32 nodes every 3–5 seconds.
- **Headers**: `X-Device-Key: medguard-device-secret-key-2026`
- **Request Body**:
```json
{
  "storage_unit_code": "UNIT-A-FRIDGE",
  "temperature": 4.3,
  "humidity": 47.5,
  "light_lux": 15.0,
  "door_open": false,
  "power_connected": true,
  "battery_level": 3.3,
  "is_offline_sync": false
}
```
- **Processing**: Automatically runs trend slope calculation, rolling Z-score anomaly detector, calculates 0–100 risk score, logs audit events, creates multi-level alerts, and broadcasts live over WebSockets.

### `POST /telemetry/sync`
Batch ingestion endpoint called upon Wi-Fi reconnection to backfill offline buffered frames.

---

## 4. Medicines & Affected Inventory

### `GET /inventory/affected/{storage_unit_id}`
Answers: *"Which medicines are affected? How serious is it? What SOP should be followed?"*
- **Response `200 OK`**:
```json
{
  "storage_unit_id": 1,
  "storage_unit_code": "UNIT-A-FRIDGE",
  "storage_unit_name": "Pharmacy Refrigerator A",
  "current_temperature": 10.6,
  "current_humidity": 68.5,
  "current_risk_score": 78.5,
  "risk_level": "HIGH_RISK",
  "incident_active": true,
  "affected_batches_count": 4,
  "total_doses_at_risk": 465,
  "affected_items": [
    {
      "medicine_id": 1,
      "medicine_name": "Insulin Glargine (Lantus)",
      "batch_id": 1,
      "batch_number": "LANT-2026-X8",
      "quantity": 80,
      "expiry_date": "2027-08-15",
      "required_min_temp": 2.0,
      "required_max_temp": 8.0,
      "light_sensitive": true,
      "deviation_description": "Temperature 10.6°C exceeds allowed maximum (8.0°C)"
    }
  ],
  "standard_operating_procedure": "STANDARD OPERATING PROCEDURE (SOP) ADVISORY:\n1. Quarantine affected storage compartment; do not discard stock automatically.\n2. Record elapsed excursion duration and peak temperature in the unit logbook.\n3. Consult product monograph / manufacturer stability data.\n4. Contact Quality Assurance Officer before returning stock to active dispensing."
}
```

---

## 5. Alerts & Auditing

### `GET /alerts/active`
Returns all active and acknowledged alerts with recommended actions and staff notes.

### `POST /alerts/{id}/acknowledge`
Staff submits inspection notes and acknowledges an alert.

### `POST /alerts/{id}/resolve`
Marks an alert as resolved with corrective action notes.

### `GET /audit/logs`
Returns the tamper-evident regulatory audit trail.

---

## 6. Reports

### `GET /reports/storage-summary?days=7`
Returns 7-day statistical compliance summary (average, max, min temp, humidity, deviation duration, alert counts).

### `GET /reports/export-csv?storage_unit_id=1&days=7`
Streams a formatted CSV download of time-series telemetry.

---

## 7. Hackathon Demo Mode

### `POST /demo/trigger-scenario`
Triggers any of the 6 judge demonstration scenarios instantly.
- **Request Body**: `{"scenario_id": 2, "unit_code": "UNIT-A-FRIDGE"}`

### `POST /demo/reset`
Resets simulation state to normal safe baseline.
