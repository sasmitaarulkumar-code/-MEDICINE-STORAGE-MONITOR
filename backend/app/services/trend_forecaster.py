from typing import List, Optional, Tuple, Dict, Any
import numpy as np

class TrendForecaster:
    """
    Predictive Early Failure Warning Engine.
    Uses Ordinary Least Squares linear regression over recent readings
    to compute temperature drift rate (°C/min) and estimate time to threshold breach.
    """

    @staticmethod
    def analyze_trend(
        readings: List[Tuple[float, float]], # List of (timestamp_seconds, temperature)
        target_max_temp: float,
        target_min_temp: float
    ) -> Dict[str, Any]:
        if len(readings) < 4:
            return {
                "has_warning": False,
                "slope_c_per_min": 0.0,
                "trend_direction": "STABLE",
                "estimated_time_to_breach_min": None,
                "confidence_percent": 0.0,
                "description": "Telemetry history calibrating."
            }

        # Convert to numpy arrays
        times = np.array([r[0] for r in readings])
        temps = np.array([r[1] for r in readings])

        # Normalize time to minutes from start of window
        t_min = (times - times[0]) / 60.0
        
        # Guard against zero variance in time
        if np.max(t_min) == 0:
            return {
                "has_warning": False,
                "slope_c_per_min": 0.0,
                "trend_direction": "STABLE",
                "estimated_time_to_breach_min": None,
                "confidence_percent": 0.0,
                "description": "Insufficient time spread."
            }

        # Linear regression slope: T = m * t + c
        n = len(t_min)
        mean_t = np.mean(t_min)
        mean_T = np.mean(temps)
        
        numerator = np.sum((t_min - mean_t) * (temps - mean_T))
        denominator = np.sum((t_min - mean_t) ** 2)

        slope = float(numerator / denominator) if denominator != 0 else 0.0
        current_temp = float(temps[-1])

        # Compute R-squared correlation for confidence
        predicted = slope * t_min + (mean_T - slope * mean_t)
        ss_res = np.sum((temps - predicted) ** 2)
        ss_tot = np.sum((temps - mean_T) ** 2)
        r_squared = float(1.0 - (ss_res / ss_tot)) if ss_tot != 0 else 0.0
        confidence = max(0.0, min(99.0, r_squared * 100.0))

        has_warning = False
        time_to_breach: Optional[float] = None
        trend_direction = "STABLE"
        description = "Temperature trajectory is stable."

        # Case 1: Continuous warming trend towards upper limit
        if slope > 0.10: # Warming faster than +0.1°C per minute
            trend_direction = "WARMING"
            if current_temp < target_max_temp:
                remaining_headroom = target_max_temp - current_temp
                time_to_breach = round(remaining_headroom / slope, 1)
                
                if time_to_breach <= 15.0 and confidence >= 50.0:
                    has_warning = True
                    description = (
                        f"Early Warning: Continuous warming trend detected (+{slope:.2f}°C/min). "
                        f"Estimated upper limit breach in {time_to_breach} mins at current trajectory. "
                        f"Confidence: {confidence:.0f}%."
                    )
                else:
                    description = f"Mild warming trend (+{slope:.2f}°C/min). Current temp: {current_temp:.1f}°C."
            else:
                has_warning = True
                description = f"Temperature has already breached max limit ({target_max_temp}°C) and continues rising (+{slope:.2f}°C/min)."

        # Case 2: Continuous cooling trend towards lower limit
        elif slope < -0.10:
            trend_direction = "COOLING"
            if current_temp > target_min_temp:
                remaining_floor = current_temp - target_min_temp
                time_to_breach = round(remaining_floor / abs(slope), 1)
                
                if time_to_breach <= 15.0 and confidence >= 50.0:
                    has_warning = True
                    description = (
                        f"Early Warning: Rapid cooling trend detected ({slope:.2f}°C/min). "
                        f"Estimated lower freezing breach in {time_to_breach} mins. "
                        f"Confidence: {confidence:.0f}%."
                    )
                else:
                    description = f"Mild cooling trend ({slope:.2f}°C/min). Current temp: {current_temp:.1f}°C."
            else:
                has_warning = True
                description = f"Temperature has fallen below min limit ({target_min_temp}°C) and continues dropping."

        return {
            "has_warning": has_warning,
            "slope_c_per_min": round(slope, 3),
            "trend_direction": trend_direction,
            "estimated_time_to_breach_min": time_to_breach,
            "confidence_percent": round(confidence, 1),
            "description": description
        }
