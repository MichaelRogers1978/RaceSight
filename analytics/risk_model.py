from __future__ import annotations

from typing import Any


def _clamp(value: float, low: float, high: float) -> float:
	return max(low, min(high, value))


def estimate_handling_and_risk(snapshot: dict[str, Any], override_risk_multiplier: float) -> dict[str, Any]:
	car = snapshot.get("car", {})
	driver = snapshot.get("driver", {})
	environment = snapshot.get("environment", {})

	speed = float(car.get("speed_kph", 210.0))
	tire_wear = float(car.get("tire_wear_pct", 20.0))
	tire_temp = float(car.get("tire_temp_c", 95.0))
	smoothness = float(driver.get("steering_smoothness", 78.0))
	stress = float(driver.get("stress_index", 45.0))
	grip = float(environment.get("grip_factor", 1.0))

	instability_events = int(max(0, round(max(0.0, speed - 250.0) / 18.0 + max(0.0, 95.0 - smoothness) / 20.0)))
	lockups = int(max(0, round(max(0.0, speed - 260.0) / 24.0)))
	off_track = int(max(0, round(max(0.0, 0.95 - grip) * 7.0)))

	handling = 92.0 - tire_wear * 0.35 - max(0.0, tire_temp - 102.0) * 0.22 - instability_events * 2.8
	handling += (smoothness - 75.0) * 0.15
	handling_score = _clamp(handling, 0.0, 100.0)

	risk = (100.0 - handling_score) * 0.55 + stress * 0.28 + lockups * 6.0 + off_track * 11.0
	risk *= max(1.0, override_risk_multiplier)
	risk_index = _clamp(risk, 0.0, 100.0)

	return {
		"handling_score": handling_score,
		"risk_index": risk_index,
		"instability_events": instability_events,
		"lockups": lockups,
		"off_track_events": off_track,
	}


def estimate_safety_status(
	race_context: dict[str, Any],
	handling_and_risk: dict[str, Any],
	traffic_model: dict[str, Any],
	override_model: dict[str, Any],
) -> dict[str, Any]:
	risk = float(handling_and_risk["risk_index"])
	yellow_sectors = race_context.get("yellow_flag_sectors", [])
	safety_car = bool(race_context.get("safety_car_active", False))
	vsc = bool(race_context.get("vsc_active", False))
	slow_car_ahead = bool(traffic_model.get("slow_car_ahead", False))
	override_detected = bool(override_model.get("override_detected", False))

	if safety_car:
		return {
			"safety_alert_active": True,
			"alert_level": "warning",
			"alert_reason": "Safety car deployed",
			"recommended_action": "Hold delta, avoid overtakes, prepare for restart",
			"enforced_mode": "safety_car",
		}

	if vsc:
		return {
			"safety_alert_active": True,
			"alert_level": "advisory",
			"alert_reason": "Virtual safety car active",
			"recommended_action": "Maintain VSC delta and conserve tires",
			"enforced_mode": "vsc",
		}

	if yellow_sectors:
		return {
			"safety_alert_active": True,
			"alert_level": "warning",
			"alert_reason": f"Yellow flag in sectors {yellow_sectors}",
			"recommended_action": "Lift and coast through yellow sectors; no overtakes",
			"enforced_mode": "yellow",
		}

	if risk >= 75.0 or (override_detected and risk >= 60.0):
		return {
			"safety_alert_active": True,
			"alert_level": "critical",
			"alert_reason": "Critical handling-risk threshold reached",
			"recommended_action": "Immediate pace reduction and conservative corner entry",
			"enforced_mode": "pit_limiter",
		}

	if slow_car_ahead and risk >= 45.0:
		return {
			"safety_alert_active": True,
			"alert_level": "advisory",
			"alert_reason": "Traffic compression with elevated risk",
			"recommended_action": "Maintain clean air gap and delay aggressive moves",
			"enforced_mode": "none",
		}

	return {
		"safety_alert_active": False,
		"alert_level": "none",
		"alert_reason": "No active safety hazards",
		"recommended_action": "Maintain target race pace",
		"enforced_mode": "none",
	}
