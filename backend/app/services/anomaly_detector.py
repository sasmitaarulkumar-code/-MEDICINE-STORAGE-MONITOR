from typing import List, Dict, Any
import numpy as np

class AnomalyDetector:
    """
    Lightweight Statistical Anomaly Detector for IoT telemetry streams.
    Computes rolling mean and standard deviation (Z-score) to catch sudden
    thermal spikes, rapid humidity changes, or erratic sensor failures.
    """

    @staticmethod
    def detect_anomalies(
        recent_values: List[float],
        current_value: float,
        metric_name: str = "Temperature",
        z_threshold: float = 3.0
    ) -> Dict[str, Any]:
        if len(recent_values) < 8:
            return {
                "is_anomaly": False,
                "z_score": 0.0,
                "mean": current_value,
                "std": 0.0,
                "anomaly_type": None,
                "details": "Collecting initial baseline."
            }

        arr = np.array(recent_values)
        mean = float(np.mean(arr))
        std = float(np.std(arr))

        # Check for physical impossibility / sensor dropout
        if metric_name == "Temperature":
            if current_value < -50.0 or current_value > 100.0:
                return {
                    "is_anomaly": True,
                    "z_score": 99.0,
                    "mean": mean,
                    "std": std,
                    "anomaly_type": "SENSOR_FAULT",
                    "details": f"Physical sensor range fault: {current_value}°C reading is out of hardware bounds."
                }
            # Sudden delta test: > 5°C jump compared to immediately preceding reading
            if abs(current_value - recent_values[-1]) > 5.0:
                return {
                    "is_anomaly": True,
                    "z_score": 5.0,
                    "mean": mean,
                    "std": std,
                    "anomaly_type": "SUDDEN_SPIKE",
                    "details": f"Abrupt {metric_name} shift: Changed by {abs(current_value - recent_values[-1]):.1f}°C in a single sample."
                }

        # Guard against zero standard deviation (perfect flatline)
        if std < 0.05:
            # If standard deviation is extremely tiny, a moderate shift is not necessarily an anomaly
            return {
                "is_anomaly": False,
                "z_score": 0.0,
                "mean": mean,
                "std": std,
                "anomaly_type": None,
                "details": "Readings are exceptionally steady."
            }

        z_score = abs(current_value - mean) / std

        is_anomaly = z_score >= z_threshold
        anomaly_type = None
        details = "Reading aligns with rolling statistical baseline."

        if is_anomaly:
            if current_value > mean:
                anomaly_type = "STATISTICAL_HIGH_OUTLIER"
                details = f"Abnormal high spike: {metric_name} is {z_score:.1f} standard deviations above recent average ({mean:.1f})."
            else:
                anomaly_type = "STATISTICAL_LOW_OUTLIER"
                details = f"Abnormal low drop: {metric_name} is {z_score:.1f} standard deviations below recent average ({mean:.1f})."

        return {
            "is_anomaly": is_anomaly,
            "z_score": round(z_score, 2),
            "mean": round(mean, 2),
            "std": round(std, 2),
            "anomaly_type": anomaly_type,
            "details": details
        }
