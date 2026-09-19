# MEDGUARD Hardware Assembly & Enclosure Guide

## 1. Hardware Pinout Table

| Peripheral | ESP32 Pin | Logic Level | Resistor | Description |
| :--- | :--- | :--- | :--- | :--- |
| **DHT22 Data** | GPIO 4 | 3.3V Digital | 10kΩ Pull-up to 3V3 | Precision temp (-40°C to +80°C) and humidity |
| **LDR Analog** | GPIO 34 (ADC1) | 0–3.3V Analog | 10kΩ Pull-down to GND | Photoresistor light intrusion detection |
| **Reed Switch** | GPIO 14 | 3.3V Digital | Internal Pull-up | Magnetic door open/closed contact |
| **Power Sense** | GPIO 35 (ADC1) | 0–2.5V Analog | 10kΩ / 10kΩ Divider | Mains AC/USB power failure sensor |
| **Active Buzzer** | GPIO 18 | 3.3V Digital | None (Direct / NPN) | Acoustic local alarms independent of Wi-Fi |
| **Green LED** | GPIO 19 | 3.3V Digital | 220Ω in series | Safe status indicator |
| **Yellow LED** | GPIO 21 | 3.3V Digital | 220Ω in series | Caution status indicator |
| **Red LED** | GPIO 22 | 3.3V Digital | 220Ω in series | Critical / Risk status indicator |

---

## 2. Circuit Diagram & Safety

```
                     +3.3V
                       │
             ┌─────────┴─────────┐
             │                   │
         [ 10kΩ ]             [ LDR ]
             │                   │
             ├───── GPIO 4       ├───── GPIO 34 (ADC)
             │                   │
         [ DHT22 ]           [ 10kΩ ]
             │                   │
            GND                 GND

    GPIO 14 ─────[ Reed Switch ]───── GND (Internal Pullup Active)

    +5V VBUS ───[ 10kΩ ]───┬───[ 10kΩ ]─── GND
                           │
                       GPIO 35 (ADC Power Sense)
```

---

## 3. Physical Demonstration Chamber (Phase 16)

1. **Chamber**: Use a small styrofoam container or insulated lunch box (20cm × 15cm × 15cm) representing a vaccine refrigerator.
2. **Door Sensor**: Glue the reed switch to the rim and attach a neodymium magnet to the lid.
3. **Lighting**: Mount the LDR facing upward inside the box. When the lid is opened, light jumps from 10 Lux to >400 Lux.
4. **Mock Medicines**: Store 2–3 labelled vials:
   - *"Insulin Glargine — DEMO ONLY"*
   - *"Hepatitis B Vaccine — DEMO ONLY"*
5. **Interactive Judge Actions**:
   - Touch warm thumb to DHT22 → temperature rises and triggers Early Warning trend banner.
   - Open lid → Door status transitions to OPEN; LDR jumps to 400 Lux.
   - Unplug USB power → Power sense triggers instant `POWER INTERRUPTION DETECTED` alarm.
