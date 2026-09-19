# MEDGUARD — Intelligent Medicine Storage Monitoring & Early Warning System

> **A Complete Hackathon-Ready IoT & AI Cold-Chain Operational Intelligence Platform**

MEDGUARD transforms routine medicine and vaccine storage monitoring from a passive, delayed alert check into an intelligent, predictive, operational decision-support platform.

---

## 1. Core Problem & Need

Medicines, biologics, and vaccines lose clinical potency or become toxic when exposed to temperatures or environmental conditions outside their specified ranges. Despite modern advances:
- **Manual Logging Risk**: Hospitals, rural health centers, and community pharmacies still rely on paper clipboards checked twice daily. A cooling compressor failure occurring at 6:00 PM remains undiscovered for 15 hours until the morning shift.
- **Trivial Threshold Alarms**: Standard commercial loggers simply beep after limits are breached (e.g. at 8.1°C), providing **zero proactive reaction time** for hospital staff to salvage irreplaceable stock.
- **No Inventory Linkage**: Conventional data loggers lack context—pharmacists are left guessing which specific batches, vials, or patient doses were compromised.

MEDGUARD continuously monitors storage conditions and provides an **early warning before serious storage failure occurs**.

---

## 2. Key Product Differentiators: 10 Operational Questions

MEDGUARD does not merely check if "Temperature > 8°C". It converts raw sensor readings into an intelligent **Medicine Storage Risk Score** that answers:
1. **What is happening?** Multi-parameter telemetry: Temperature, humidity, ambient light intrusion, door open/closed status, and primary AC mains voltage.
2. **Why is it happening?** Root cause isolation: Gasket seal breach, door left ajar, AC power blackout, or refrigeration compressor decline.
3. **How serious is it?** A 0–100 Weighted Operational Storage Risk Score (Safe: 0–30, Caution: 31–60, High Risk: 61–80, Critical: 81–100).
4. **Which medicines are affected?** Live inventory impact tracing down to individual batch numbers, dose counts, expiry dates, and manufacturer storage criteria.
5. **Who needs to act?** Role-based routing: Duty Nurse, Chief Pharmacist, or Biomedical Engineering Technician.
6. **How much time is available to respond?** Predictive linear regression slope calculations estimate **Time-to-Threshold breach** while the unit is still within safe limits.
7. **What should the user do?** Clear SOP guidance (quarantine instructions, monograph stability lookups, and QA escalation).
8. **Has this happened before?** Historical thermal cycling tracking over the previous 24 hours to flag recurring mechanical compressor faults.
9. **Is the problem temporary or becoming dangerous?** Rolling window persistence checks and Z-score anomaly detection.
10. **What storage improvements are needed?** Automated 7-day compliance reports, thermal stability indices, and CSV audit exports.

---

## 3. System Architecture

```
[ PHYSICAL / DEMO CHAMBER ]
   ESP32 MCU (Dual-Core 240MHz, FreeRTOS)
   ├── DHT22 (Precision Ambient Temperature & Humidity)
   ├── Photoresistor LDR (Cabinet Light Intrusion / Seal Integrity)
   ├── Magnetic Reed Switch (Door Latch State)
   ├── Mains Voltage Divider (AC Power Cut Sensor)
   ├── Piezo Buzzer & RGB Status LEDs (Autonomous Local Failsafes)
   └── LittleFS / RAM Ring Buffer (Offline Persistence up to 2,000 records)
           │
           │  HTTP POST /api/v1/telemetry/ingest (Online)
           │  HTTP POST /api/v1/telemetry/sync   (Catch-up upon reconnect)
           ▼
[ BACKEND CORE (FastAPI + Python 3.11) ]
   ├── Ingestion & Validation Pipeline
   ├── 0–100 Operational Risk Score Engine
   ├── Predictive Trend Forecaster (OLS Linear Regression Slope)
   ├── Rolling Z-Score Anomaly Detector (|Z| > 3.0)
   ├── Multi-Level Alert Lifecycle Manager (Level 1 Warning / L2 High / L3 Critical)
   ├── Tamper-Evident Audit Trail Service
   ├── SQLite Database (WAL Mode for Concurrent High-Speed I/O)
   └── WebSocket Live Broadcast Hub (/api/v1/ws/live)
           │
           │  Real-Time Bi-Directional WebSockets + REST API
           ▼
[ HEALTHCARE OPERATIONAL DASHBOARD (HTML5 + Tailwind + Recharts / Chart.js) ]
   ├── Multi-Storage Unit Monitor (Fridges, Freezers, Ambient Cabinets)
   ├── Real-Time Telemetry Stream Graphs & Boundary Lines
   ├── Potentially Affected Inventory Inspector & Batch Tracer
   ├── Regulatory Compliance Audit Trail & Acknowledgement Modals
   ├── 7-Day Statistical Cold-Chain Report Generator (PDF / CSV)
   └── Interactive 3-Minute Hackathon Demo Controller
```

---

## 4. Hardware Bill of Materials (BOM)

| Component | Function | Pins | Cost |
| :--- | :--- | :--- | :--- |
| **ESP32 DevKit V1** | Dual-core processing & Wi-Fi communication | -- | \$4.50 |
| **DHT22 / AM2302** | Temperature (-40°C to +80°C) & Relative Humidity | GPIO 4 | \$3.50 |
| **LDR Photoresistor** | Detects door opened or broken light gasket | GPIO 34 (ADC1) | \$0.20 |
| **Magnetic Reed Switch** | Digital door open/close detection (debounced) | GPIO 14 (Pullup) | \$1.20 |
| **Active Piezo Buzzer** | Acoustic local alarm (independent of Wi-Fi) | GPIO 18 | \$0.60 |
| **RGB Status LED** | Visual state indicator (Green/Yellow/Red) | GPIO 19, 21, 22 | \$0.30 |
| **Voltage Divider (10k/10k)** | Detects AC mains power outage | GPIO 35 (ADC1) | \$0.40 |
| **Total BOM Cost** | | | **~\$14.70** |

---

## 5. Software & Algorithm Details

### A. 0–100 Operational Risk Formula
$$\text{RiskScore} = \min\left(100, \; 0.35 \cdot S_T + 0.20 \cdot S_D + 0.20 \cdot S_P + 0.10 \cdot S_H + 0.05 \cdot S_L + 0.10 \cdot S_R\right)$$
- $S_T$: Temperature deviation penalty multiplied by excursion duration.
- $S_D$: Door open duration ($0$ if $<45\text{s}$, $45$ if $<180\text{s}$, $100$ if $>3\text{min}$).
- $S_P$: Primary power state ($0$ if connected, $100$ if power failure).
- $S_H$: Humidity deviation penalty.
- $S_L$: Light intrusion inside sealed medicine compartment.
- $S_R$: Historical recurrence count of excursions in the past 24 hours.

### B. Predictive Early Failure Warning
$$\text{Slope } m = \frac{N \sum (t_i T_i) - \sum t_i \sum T_i}{N \sum t_i^2 - (\sum t_i)^2}$$
- When slope $m > +0.10^\circ\text{C}/\text{min}$ and $T < T_{\max}$, MEDGUARD calculates:
$$t_{\text{breach}} = \frac{T_{\max} - T_{\text{current}}}{m}$$
- Displays: *"Early Warning: Continuous warming trend (+0.45°C/min). Estimated upper limit breach in 2.2 minutes at current trajectory."*

### C. Rolling Z-Score Anomaly Detection
$$Z = \frac{|T_t - \mu_{W}|}{\sigma_W}$$
- Detects sensor disconnects, electrical faults, and rapid thermal shock before limits are violated.

---

## 6. Installation & Quick Start

### Quick Launch (Windows)
Double-click:
```cmd
run_medguard.bat
```
This automatically verifies the database, seeds default users/units/medicines, starts Uvicorn at `http://127.0.0.1:8000`, and opens your browser directly to the dashboard!

### Manual Launch
```bash
# 1. Activate Virtual Environment
cd backend
.venv\Scripts\activate

# 2. Seed Database
python seed_data.py

# 3. Run Test Suite
python -m pytest -v tests

# 4. Start Server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open in Browser:
- **Landing Page**: `http://127.0.0.1:8000/`
- **Operational Dashboard**: `http://127.0.0.1:8000/dashboard`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`

---

## 7. Demo Mode Instructions (Judge 3-Minute Script)

On the dashboard, use the floating **Hackathon Demo Controller** in the bottom-right corner:
1. **Scenario 1 — Normal Baseline**: Unit at 4.2°C, Status: **SAFE** (Risk: 12).
2. **Scenario 2 — Trend Warning**: System detects continuous warming (+0.45°C/min) and estimates limit breach in 1.3 mins. Status: **CAUTION** (Risk: 45).
3. **Scenario 3 — Critical Excursion (>10°C)**: Temperature hits 10.6°C. Level 2 Alert trips. Click **"Check Affected Inventory"** to display batches and SOP guidance.
4. **Scenario 4 — Door Left Ajar**: Door state transitions to OPEN for >3 minutes. Lux spikes to 480. Acoustic alarm sounds.
5. **Scenario 5 — Power Outage**: Primary AC drops. Flashing `POWER INTERRUPTION DETECTED` displays.
6. **Scenario 6 — Full Recovery**: Baseline restored (4.4°C). Operator acknowledges alert and logs inspection notes into the audit trail.

---

## 8. Responsible Design & Regulatory Compliance

> [!IMPORTANT]
> **Regulatory Disclaimer**: MEDGUARD monitors storage environmental integrity. It does **NOT** provide medical diagnosis or make automated determinations regarding clinical drug efficacy. In case of storage deviation, operators are guided to follow official pharmacopeia guidelines (USP <1079>, WHO TRS 961) and quality procedures.
