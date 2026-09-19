# MEDGUARD — 3-Minute Hackathon Judge Demo Script

> **Goal**: Show a real, functioning end-to-end IoT and AI healthcare platform in under 180 seconds.

---

## Preparation (Before Judges Arrive)
1. Double-click `run_medguard.bat`.
2. Ensure the dashboard is open at `http://127.0.0.1:8000/dashboard`.
3. Locate the **Hackathon Demo Controller** in the bottom-right corner.
4. Have your physical demonstration box plugged in or ready to display.

---

## 3-Minute Execution Timeline

### 0:00 – 0:30: The Hook & The Problem
> *"Judges, over $35 billion worth of vaccines and biologics are discarded each year due to broken cold chains. Most clinics still rely on clipboard checks twice a day. When a refrigerator door fails overnight, nobody knows until the morning, when it's already too late. Existing loggers just beep after limits are breached. We built **MEDGUARD** to warn healthcare teams before excursions occur."*

### 0:30 – 1:00: Scenario 1 — Safe Baseline & Multi-Storage
- Click **"1. Normal Baseline"** on the Demo Controller.
- Point to the screen:
  - *"Here is our live dashboard. Storage Unit A (Pharmacy Refrigerator) is at 4.2°C, 48% RH, Door Closed, Power Healthy. The Operational Risk Score is 12 (SAFE)."*
  - Show the multi-storage tabs: *"We can simultaneously monitor Pharmacy Fridges, Vaccine Freezers, and Ambient Medicine Cabinets across different hospital wards."*

### 1:00 – 1:30: Scenario 2 — Predictive Early Failure Warning (The Key Differentiator!)
- Click **"2. Early Trend"**.
- Point to the AI Alert Banner that immediately appears:
  - *"Watch this: the temperature is only at 7.4°C—still inside the safe 8.0°C limit! But our OLS regression trend engine has detected a continuous warming rate of +0.45°C/min. The system warns us: 'Continuous warming trend detected. Estimated breach in 1.3 minutes. Status: CAUTION (Risk: 45)'. Staff now have time to act before medicines are spoiled!"*

### 1:30 – 2:00: Scenario 3 — Critical Excursion & Affected Inventory View
- Click **"3. Excursion (>10°C)"**.
- Notice the alarm sound, red border glow, and status change to **HIGH RISK (Risk: 82)**.
- Click **"Check Affected Inventory"**:
  - *"Now comes our second differentiator: In conventional systems, a nurse just sees a red number. In MEDGUARD, one click opens the Potentially Affected Inventory view. It reveals exactly 4 batches, 465 doses—including Insulin Glargine and Hepatitis B Vaccine—at risk, along with official pharmacopeia SOP guidance to quarantine and inspect rather than discard."*
- Click **Dismiss**.

### 2:00 – 2:30: Scenarios 4 & 5 — Door Ajar & Power Failure
- Click **"4. Door Ajar"**:
  - *"If a nurse leaves the refrigerator door open, light jumps to 480 Lux and door state changes to OPEN. When left open for >3 minutes, local buzzer sounds and risk increases to 85."*
- Click **"5. Power Outage"**:
  - *"If AC mains power is cut, our hardware sense trips immediately. The dashboard displays a flashing 'POWER INTERRUPTION DETECTED' banner and starts the battery backup timer."*

### 2:30 – 3:00: Scenario 6 — Recovery & Regulatory Audit Trail
- Click **"6. Recovery"**.
  - *"When conditions normalize, temperature recovers to 4.4°C. On the alert card, staff can click 'Acknowledge', type in their inspection notes ('Door latch closed securely'), and mark the alert resolved."*
- Click **"Audit Trail"** in the top navigation:
  - *"Every sensor event, threshold change, and staff acknowledgement is saved in a tamper-evident audit log for FDA and WHO compliance. And under 'Reports', a 7-day statistical compliance summary can be exported as a CSV or printed as a PDF."*
- Conclude:
  - *"MEDGUARD delivers real IoT hardware, edge resilience, predictive intelligence, and direct inventory impact for safer healthcare. Thank you!"*
