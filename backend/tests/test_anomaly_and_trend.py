from app.services.trend_forecaster import TrendForecaster
from app.services.anomaly_detector import AnomalyDetector

def test_trend_forecaster_warming():
    # Simulate temperatures rising at +0.3°C per minute: 5.0, 5.3, 5.6, 5.9, 6.2
    # At 60s intervals
    series = [(i * 60, 5.0 + i * 0.3) for i in range(8)]
    res = TrendForecaster.analyze_trend(series, target_max_temp=8.0, target_min_temp=2.0)
    
    assert res["trend_direction"] == "WARMING"
    assert res["slope_c_per_min"] > 0.25
    assert res["estimated_time_to_breach_min"] is not None
    assert res["estimated_time_to_breach_min"] > 0

def test_trend_forecaster_stable():
    series = [(i * 60, 4.2 + (i % 2) * 0.05) for i in range(8)]
    res = TrendForecaster.analyze_trend(series, target_max_temp=8.0, target_min_temp=2.0)
    assert res["has_warning"] is False

def test_anomaly_detector_spike():
    baseline = [4.1, 4.2, 4.1, 4.3, 4.2, 4.1, 4.2, 4.2]
    # Current value suddenly leaps by 6°C
    res = AnomalyDetector.detect_anomalies(baseline, current_value=10.2, metric_name="Temperature")
    assert res["is_anomaly"] is True
    assert res["anomaly_type"] in ["SUDDEN_SPIKE", "STATISTICAL_HIGH_OUTLIER"]

def test_anomaly_detector_normal():
    baseline = [4.1, 4.2, 4.1, 4.3, 4.2, 4.1, 4.2, 4.2]
    res = AnomalyDetector.detect_anomalies(baseline, current_value=4.25, metric_name="Temperature")
    assert res["is_anomaly"] is False
