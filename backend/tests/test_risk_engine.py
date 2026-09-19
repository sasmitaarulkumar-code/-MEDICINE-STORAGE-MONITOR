import pytest
from app.services.risk_engine import RiskScoreEngine

def test_risk_score_safe():
    res = RiskScoreEngine.calculate_score(
        temperature=4.2,
        humidity=45.0,
        door_open=False,
        door_open_seconds=0,
        power_connected=True,
        light_lux=15.0,
        min_temp=2.0,
        max_temp=8.0,
        min_humid=30.0,
        max_humid=65.0
    )
    assert res["status"] == "SAFE"
    assert res["risk_score"] <= 30.0

def test_risk_score_temperature_excursion():
    res = RiskScoreEngine.calculate_score(
        temperature=11.5, # 3.5°C over max limit
        humidity=50.0,
        door_open=False,
        door_open_seconds=0,
        power_connected=True,
        light_lux=15.0,
        min_temp=2.0,
        max_temp=8.0,
        min_humid=30.0,
        max_humid=65.0
    )
    assert res["risk_score"] > 20.0
    assert res["breakdown"]["temperature_risk"] > 50.0

def test_risk_score_power_failure():
    res = RiskScoreEngine.calculate_score(
        temperature=5.0,
        humidity=45.0,
        door_open=False,
        door_open_seconds=0,
        power_connected=False, # Mains power failed
        light_lux=0.0,
        min_temp=2.0,
        max_temp=8.0,
        min_humid=30.0,
        max_humid=65.0
    )
    assert res["breakdown"]["power_risk"] == 100.0
    assert res["risk_score"] >= 20.0

def test_risk_score_door_prolonged_open():
    res = RiskScoreEngine.calculate_score(
        temperature=7.5,
        humidity=60.0,
        door_open=True,
        door_open_seconds=240, # 4 minutes open
        power_connected=True,
        light_lux=400.0,
        min_temp=2.0,
        max_temp=8.0,
        min_humid=30.0,
        max_humid=65.0
    )
    assert res["breakdown"]["door_risk"] == 100.0
    assert res["risk_score"] >= 20.0
