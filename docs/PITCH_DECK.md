# MEDGUARD Hackathon Presentation Deck (12 Slides)

---

### SLIDE 1: Problem
- **Headline**: \$35 Billion in Wasted Vaccines & Biologics Annually
- **Subhead**: A single temperature excursion can render an entire refrigerator of insulin, vaccines, and biologics ineffective or unsafe.
- **Key Visual**: Manual clipboard check vs broken cold-chain refrigerator.

---

### SLIDE 2: Why Current Monitoring Fails
- **Two Major Vulnerabilities**:
  1. *Delayed Detection*: Manual clipboard checks twice daily leave 12-to-15 hour blind spots.
  2. *Trivial Alerts*: Standard loggers merely beep *after* the temperature crosses 8.0°C, leaving zero reaction time for hospital staff.
- **Missing Link**: No inventory context—nurses don't know which specific batches were compromised.

---

### SLIDE 3: Our Solution — MEDGUARD
- **Tagline**: Intelligent Medicine Storage Monitoring & Early Warning System.
- **Core Value**: Converts raw telemetry into proactive operational intelligence. Warns staff *before* failure occurs, calculates a 0–100 risk score, and maps excursions directly to affected medicine batches.

---

### SLIDE 4: How MEDGUARD Works
- **Multi-Sensor Acquisition**: Continuous measurement of Temperature, Humidity, Light Intrusion, Door Latch State, and AC Mains Power.
- **Autonomous Local Failsafe**: Buzzer and RGB LEDs trigger locally on the ESP32 even during total Wi-Fi blackouts.
- **Intelligent Cloud Engine**: Computes real-time risk scores and predicts time-to-threshold breaches.

---

### SLIDE 5: Architecture
- **Hardware**: ESP32 MCU + DHT22 + LDR + Magnetic Reed Switch + Mains Voltage Divider.
- **Edge Layer**: FreeRTOS Dual-Tasking + Flash-based Offline Ring Buffer (2,000 readings).
- **Backend Core**: FastAPI (Python 3.11) + SQLite WAL Mode + WebSockets.
- **Frontend Portal**: Responsive Healthcare Dashboard with Live Boundary Charts and Batch Impact Inspector.

---

### SLIDE 6: Innovation Highlights
- **Predictive Early Warning**: OLS linear regression slope detects warming trends (+0.45°C/min) and estimates minutes to threshold breach.
- **Affected Inventory View**: Directly matches storage violations against batch numbers, dose counts, expiry dates, and SOP guidance.
- **0–100 Operational Risk Score**: Multi-factor weighted index (temperature, humidity, door duration, power state, and 24h recurrence).

---

### SLIDE 7: Working Prototype
- **Hardware Node**: Housed in a custom compact medicine storage compartment with live sensors and actuators.
- **Demonstrated Response**: Physical door opening immediately causes light sensor to spike, transitions dashboard state to OPEN, and recalculates risk.

---

### SLIDE 8: AI & Anomaly Detection
- **Rolling Z-Score Anomaly Detector**: Flags statistical outliers ($|Z| > 3.0$), abrupt thermal shocks, or probe disconnects.
- **Trend Regression**: Identifies continuous gradual warming before limits are breached, giving staff 5–15 minutes of actionable reaction time.

---

### SLIDE 9: Real-World Impact
- **Cost Reduction**: Prevents \$100,000+ single-incident pharmaceutical losses in hospital pharmacy cold rooms.
- **Patient Safety**: Ensures compromised biologics or frozen vaccines are never mistakenly administered to patients.
- **Staff Accountability**: Time-stamped staff acknowledgements and corrective inspection logs.

---

### SLIDE 10: Scalability & Commercial Model
- **Hardware Kit Cost**: Under \$15 per storage unit.
- **Plug-and-Play Provisioning**: Automatically registers new storage units upon first telemetry packet.
- **Multi-Tenant Deployment**: Supports hospital-wide deployments across pharmacies, clinics, laboratories, and mobile vaccine carriers.

---

### SLIDE 11: Limitations & Responsible Design
- **Important Disclaimer**: MEDGUARD monitors storage environmental integrity. It does **not** make clinical determinations regarding pharmaceutical efficacy or whether a drug can be safely injected.
- **Human in the Loop**: Guides staff to follow official monographs (USP <1079>, WHO TRS 961) and consult QA officers.

---

### SLIDE 12: Live Demonstration & Summary
- **Live 3-Minute Demo**:
  1. Safe Baseline (Risk: 12)
  2. Predictive Warming Trend (Caution: 45)
  3. Excursion & Affected Batch View (High Risk: 82)
  4. Prolonged Door Ajar
  5. Power Interruption Event
  6. Recovery & Regulatory Audit Trail
- **Call to Action**: Smarter, safer medicine storage starts with early warning.
