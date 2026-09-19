#!/usr/bin/env python3
"""
MEDGUARD — IoT Sensor Node Simulator
Simulates an ESP32 hardware node streaming real-time telemetry or replaying
historical offline batches to the MEDGUARD backend.
"""

import time
import math
import random
import requests
import argparse
import sys

DEFAULT_BACKEND = "http://127.0.0.1:8000"
DEVICE_KEY = "medguard-device-secret-key-2026"

class ESP32Simulator:
    def __init__(self, backend_url=DEFAULT_BACKEND, unit_code="UNIT-A-FRIDGE"):
        self.backend_url = backend_url.rstrip("/")
        self.unit_code = unit_code
        self.temp_base = 4.2       # Target refrigerator temperature in °C
        self.humidity_base = 48.0  # Relative humidity in %
        self.door_open = False
        self.power_connected = True
        self.battery_level = 3.3
        self.offline_mode = False
        self.offline_queue = []
        self.step = 0

    def get_telemetry_packet(self, temp_override=None, door_override=None, power_override=None):
        self.step += 1
        
        # Subtle sensor noise
        jitter_temp = (random.random() - 0.5) * 0.2
        jitter_humid = (random.random() - 0.5) * 1.0

        if temp_override is not None:
            temp = temp_override
        else:
            temp = self.temp_base + jitter_temp

        if door_override is not None:
            door = door_override
        else:
            door = self.door_open

        if power_override is not None:
            pwr = power_override
        else:
            pwr = self.power_connected

        # If door is open, light increases dramatically and temperature drifts up
        if door:
            lux = random.uniform(350.0, 550.0)
            temp += 0.8
        else:
            lux = random.uniform(5.0, 25.0)

        # Humidity calculation
        humid = self.humidity_base + jitter_humid
        if door:
            humid += 8.0

        return {
            "storage_unit_code": self.unit_code,
            "temperature": round(temp, 2),
            "humidity": round(humid, 2),
            "light_lux": round(lux, 1),
            "door_open": door,
            "power_connected": pwr,
            "battery_level": round(self.battery_level, 2),
            "is_offline_sync": False
        }

    def send_packet(self, packet):
        url = f"{self.backend_url}/api/v1/telemetry/ingest"
        headers = {
            "Content-Type": "application/json",
            "X-Device-Key": DEVICE_KEY
        }
        try:
            resp = requests.post(url, json=packet, headers=headers, timeout=3)
            return resp.status_code in (200, 201), resp.text
        except Exception as e:
            return False, str(e)

    def sync_offline_batch(self):
        if not self.offline_queue:
            return True, "Queue empty"
        
        url = f"{self.backend_url}/api/v1/telemetry/sync"
        headers = {
            "Content-Type": "application/json",
            "X-Device-Key": DEVICE_KEY
        }
        payload = {
            "storage_unit_code": self.unit_code,
            "readings": self.offline_queue
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=5)
            if resp.status_code in (200, 201):
                count = len(self.offline_queue)
                self.offline_queue.clear()
                return True, f"Successfully synced {count} cached offline records"
            return False, resp.text
        except Exception as e:
            return False, str(e)

    def run_stream(self, interval_sec=3.0, iterations=None):
        print(f"[SIMULATOR] Starting ESP32 Stream for '{self.unit_code}' -> {self.backend_url}")
        print("[SIMULATOR] Press Ctrl+C to terminate.")
        count = 0
        try:
            while iterations is None or count < iterations:
                packet = self.get_telemetry_packet()
                if self.offline_mode:
                    self.offline_queue.append(packet)
                    print(f"[OFFLINE-BUFFER] Cached reading #{len(self.offline_queue)} | Temp: {packet['temperature']}°C")
                else:
                    success, msg = self.send_packet(packet)
                    if success:
                        print(f"[INGEST OK] Temp: {packet['temperature']}°C | Humid: {packet['humidity']}% | Lux: {packet['light_lux']} | Door: {'OPEN' if packet['door_open'] else 'CLOSED'} | Pwr: {'ON' if packet['power_connected'] else 'OFF'}")
                    else:
                        print(f"[INGEST FAILED -> BUFFERING] Error: {msg}")
                        self.offline_queue.append(packet)

                count += 1
                time.sleep(interval_sec)
        except KeyboardInterrupt:
            print("\n[SIMULATOR] Stopped by user.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MEDGUARD ESP32 Sensor Simulator")
    parser.add_argument("--url", default=DEFAULT_BACKEND, help="Backend URL")
    parser.add_argument("--unit", default="UNIT-A-FRIDGE", help="Storage Unit Code")
    parser.add_argument("--interval", type=float, default=3.0, help="Interval in seconds")
    parser.add_argument("--offline", action="store_true", help="Start in offline mode")
    args = parser.parse_args()

    sim = ESP32Simulator(backend_url=args.url, unit_code=args.unit)
    sim.offline_mode = args.offline
    sim.run_stream(interval_sec=args.interval)
