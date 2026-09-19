# MEDGUARD — Intelligent Medicine Storage Monitoring & Early Warning System

[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Python: 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal.svg)](https://fastapi.tiangolo.com)
[![IoT: ESP32](https://img.shields.io/badge/Hardware-ESP32-red.svg)](firmware/)
[![Tests: 14 Passed](https://img.shields.io/badge/Tests-14%20Passed-brightgreen.svg)](backend/tests/)

> **A Complete Hackathon-Ready IoT & AI Cold-Chain Operational Intelligence Platform**

MEDGUARD transforms routine medicine and vaccine storage monitoring from a passive, delayed alert check into an intelligent, predictive, operational decision-support platform.

---

## ⚡ Quick 1-Click Launch (Windows)

Simply double-click:
```cmd
run_medguard.bat
```
This automatically verifies the SQLite database, seeds default users, units, and medicines, starts the FastAPI server on `http://127.0.0.1:8000`, and opens your browser directly to the dashboard!

---

## 📁 Repository Structure

- `backend/`: FastAPI core, SQLite with WAL mode, risk engine, anomaly detector, predictive trend forecaster, and WebSocket hub.
- `firmware/`: ESP32 Arduino C++ firmware with FreeRTOS multitasking, LittleFS offline ring buffer, sensor simulator, and wiring schematics.
- `frontend/`: Single Page Application with Tailwind CSS, Recharts, real-time WebSocket updates, affected batch inspector, and 3-minute hackathon demo panel.
- `docs/`: Comprehensive technical architecture (`ARCHITECTURE.md`), API specification (`API.md`), hardware wiring (`HARDWARE.md`), judge demo script (`DEMO.md`), 12-slide pitch deck (`PITCH_DECK.md`), and judge Q&A guide (`JUDGE_QA.md`).

---

## 🧪 Automated Testing

All 14 unit and integration tests pass with 100% success:
```bash
cd backend
.venv\Scripts\activate
python -m pytest -v tests
```

---

## 🩺 Responsible Design Disclaimer
MEDGUARD monitors environmental storage conditions. It does **NOT** determine clinical drug efficacy or authorize patient administration. Qualified healthcare personnel must verify medicines against official monographs (USP <1079>, WHO TRS 961).
