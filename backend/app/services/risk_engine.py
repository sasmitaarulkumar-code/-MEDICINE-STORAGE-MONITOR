import math
from datetime import datetime, timedelta
from typing import Dict, Any

class RiskScoreEngine:
    """
    Computes the 0-100 Operational Medicine Storage Risk Score.
    Note: Operational risk indicator only; not clinical efficacy determination.
    """
    
    @staticmethod
    def calculate_score(
        temperature: float,
        humidity: float,
        door_open: bool,
        door_open_seconds: int,
        power_connected: bool,
        light_lux: float,
        min_temp: float,
        max_temp: float,
        min_humid: float,
        max_humid: float,
        recent_alert_count_24h: int = 0
    ) -> Dict[str, Any]:
        # 1. Temperature Deviation Score (Weight: 35%)
        s_temp = 0.0
        if temperature < min_temp:
            dev = min_temp - temperature
            s_temp = min(100.0, dev * 20.0)
        elif temperature > max_temp:
            dev = temperature - max_temp
            s_temp = min(100.0, dev * 20.0)
        
        # 2. Door Open Duration Score (Weight: 20%)
        s_door = 0.0
        if door_open:
            if door_open_seconds < 45:
                s_door = 15.0  # Normal routine access
            elif door_open_seconds < 180:
                s_door = 45.0  # Warning level door ajar
            else:
                s_door = 100.0 # Prolonged breach
        
        # 3. Power Interruption Score (Weight: 20%)
        s_power = 0.0 if power_connected else 100.0
        
        # 4. Humidity Deviation Score (Weight: 10%)
        s_humid = 0.0
        if humidity < min_humid:
            s_humid = min(100.0, (min_humid - humidity) * 3.0)
        elif humidity > max_humid:
            s_humid = min(100.0, (humidity - max_humid) * 3.0)
            
        # 5. Light Intrusion Score (Weight: 5%)
        # Normal inside dark fridge is < 30 lux. If > 200 lux while door thought to be closed, gasket issue
        s_light = 0.0
        if not door_open and light_lux > 150.0:
            s_light = 60.0
        elif door_open and light_lux > 300.0:
            s_light = 30.0

        # 6. Historical Fluctuation / Recurrence Score (Weight: 10%)
        s_history = min(100.0, recent_alert_count_24h * 25.0)

        # Weighted Sum
        raw_score = (
            0.35 * s_temp +
            0.20 * s_door +
            0.20 * s_power +
            0.10 * s_humid +
            0.05 * s_light +
            0.10 * s_history
        )
        final_score = round(min(100.0, max(0.0, raw_score)), 1)

        # Categorization
        if final_score <= 30.0:
            status = "SAFE"
        elif final_score <= 60.0:
            status = "CAUTION"
        elif final_score <= 80.0:
            status = "HIGH_RISK"
        else:
            status = "CRITICAL"

        return {
            "risk_score": final_score,
            "status": status,
            "breakdown": {
                "temperature_risk": round(s_temp, 1),
                "door_risk": round(s_door, 1),
                "power_risk": round(s_power, 1),
                "humidity_risk": round(s_humid, 1),
                "light_risk": round(s_light, 1),
                "history_risk": round(s_history, 1)
            }
        }
