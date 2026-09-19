# MEDGUARD — Hardware Wiring & Assembly Specification

This guide details the physical wiring, bill of materials, and circuit safety precautions for the MEDGUARD ESP32 IoT Node.

---

## 1. Bill of Materials (BOM)

| Item | Component | Qty | Purpose / Specification | Approximate Cost |
| :--- | :--- | :--- | :--- | :--- |
| **1** | ESP32 DevKit V1 (30-pin) | 1 | Dual-core 240MHz MCU with 2.4GHz Wi-Fi + BLE | \$4.50 |
| **2** | DHT22 / AM2302 Sensor | 1 | Precision temp (-40°C to +80°C, ±0.5°C) & humidity (0–100% RH) | \$3.50 |
| **3** | Photoresistor (LDR, 5mm) | 1 | Light intrusion detection inside dark medicine cabinets | \$0.20 |
| **4** | Magnetic Reed Switch + Magnet | 1 | Door open/closed sensor (normally open or normally closed) | \$1.20 |
| **5** | Active Piezo Buzzer (5V/3.3V) | 1 | Local acoustic failsafe alarms (independent of cloud/Wi-Fi) | \$0.60 |
| **6** | RGB LED (Common Cathode) | 1 | Multi-state visual alert (Green = Safe, Yellow = Caution, Red = Risk) | \$0.30 |
| **7** | Resistors: 10kΩ (×3), 220Ω (×3) | 6 | Pull-up, voltage divider, and LED current limiting | \$0.40 |
| **8** | Half-size Breadboard & Jumper Wires| 1 | Prototyping connection block | \$2.00 |
| **9** | Micro-USB Cable + 5V 1A Adapter | 1 | Primary power supply | \$2.00 |
| **Total** | | | **Complete Hardware Kit** | **~\$14.70** |

---

## 2. Complete Pinout & Wiring Table

```
      ESP32 DEVKIT V1
      +---------------+
  3V3 | [ ]       [ ] | GND
  EN  | [ ]       [ ] | GPIO 23
  VP  | [ ]       [ ] | GPIO 22 ----> Red LED Anode (via 220Ω)
  VN  | [ ]       [ ] | GPIO 1
  D34 | [x]       [ ] | GPIO 3
  D35 | [x]       [ ] | GPIO 21 ----> Yellow LED Anode (via 220Ω)
  D32 | [ ]       [ ] | GPIO 19 ----> Green LED Anode (via 220Ω)
  D33 | [ ]       [ ] | GPIO 18 ----> Buzzer (+)
  D25 | [ ]       [ ] | GPIO 5
  D26 | [ ]       [ ] | GPIO 17
  D27 | [ ]       [ ] | GPIO 16
  D14 | [x]       [ ] | GPIO 4  ----> DHT22 Data (with 10kΩ pull-up)
  D12 | [ ]       [ ] | GPIO 0
  D13 | [ ]       [ ] | GPIO 2
  GND | [ ]       [ ] | GPIO 15
      +---------------+
```

### Pin-by-Pin Connections

#### 1. DHT22 (Temperature & Humidity)
- **Pin 1 (VCC)**: Connect to ESP32 **3V3**.
- **Pin 2 (Data)**: Connect to ESP32 **GPIO 4**.
- **Pull-up Resistor**: Place a **10kΩ resistor** between Pin 1 (VCC) and Pin 2 (Data).
- **Pin 4 (GND)**: Connect to ESP32 **GND**. *(Note: Pin 3 of DHT22 is not connected).*

#### 2. LDR Photoresistor (Light Intrusion)
- Connect one leg of LDR to ESP32 **3V3**.
- Connect the other leg of LDR to ESP32 **GPIO 34 (ADC1)**.
- Connect a **10kΩ pull-down resistor** from **GPIO 34** to **GND** (forms a voltage divider).
- *Behavior*: In darkness (closed cabinet), GPIO 34 reads near 0V (~0 ADC). When the door opens and light enters, resistance drops, and GPIO 34 reads 1.5V–3.0V (~2000–3800 ADC).

#### 3. Magnetic Reed Switch (Door Open/Close)
- Connect one terminal of the reed switch to ESP32 **GPIO 14**.
- Connect the other terminal to **GND**.
- The firmware enables ESP32's internal pull-up resistor on GPIO 14 (`INPUT_PULLUP`).
- *Behavior*:
  - Door Closed (Magnet adjacent): Switch closes → GPIO 14 pulled to **LOW (0V)**.
  - Door Ajar / Opened (Magnet moved away): Switch opens → GPIO 14 pulled to **HIGH (3.3V)**.

#### 4. Power Sense Circuit (Mains / USB Interruption)
- Form a 2:1 voltage divider with two **10kΩ resistors**:
  - Top leg connected to 5V VBUS rail.
  - Middle junction connected to ESP32 **GPIO 35 (ADC1)**.
  - Bottom leg connected to **GND**.
- *Behavior*: When 5V mains is connected, GPIO 35 reads ~2.5V (~3100 ADC). If power is unplugged and the ESP32 is sustained briefly by a backup capacitor or Li-Po battery, GPIO 35 drops to 0V, immediately flagging `POWER INTERRUPTION DETECTED`.

#### 5. Local Failsafe Actuators (Buzzer & RGB Status LEDs)
- **Buzzer (+)**: Connect to ESP32 **GPIO 18**. Buzzer (-) to **GND**.
- **Green LED**: Anode to **GPIO 19** via **220Ω resistor**. Cathode to **GND** (Safe state).
- **Yellow LED**: Anode to **GPIO 21** via **220Ω resistor**. Cathode to **GND** (Caution state).
- **Red LED**: Anode to **GPIO 22** via **220Ω resistor**. Cathode to **GND** (Critical state).

---

## 3. Physical Demonstration Box (Phase 16)

For hackathon judging, build a miniature model representing a pharmacy refrigerator:
1. **Chamber**: A small styrofoam cooler or acrylic container (approx. 20cm × 15cm × 15cm).
2. **Door Setup**: Mount the reed switch on the rim and the small neodymium magnet on the lid.
3. **Medicine Storage**: Place 2–3 labelled mock medicine vials inside (e.g., *"Insulin Glargine — DEMO ONLY"*).
4. **Trigger Actions for Judges**:
   - **Test Normal**: Keep lid closed → Green LED lit, Dashboard shows SAFE (4.2°C).
   - **Test Door Ajar**: Lift lid → Internal LDR detects light, Reed switch opens → Dashboard highlights Door Open, yellow LED illuminates.
   - **Test Temp Spike**: Place a hand warmer or warm thumb onto the DHT22 casing → Dashboard shows live temperature climbing, triggers Early Warning trend warning, then Level 2 High Risk alert.
