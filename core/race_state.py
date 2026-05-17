from __future__ import annotations

from typing import Any

from analytics.fatigue_model import estimate_driver_state, estimate_fatigue_hydration
from analytics.outcome_projection import (
	estimate_outcome_projection,
	estimate_pit_strategy,
	estimate_traffic_model,
)
from analytics.override_model import estimate_driver_override
from analytics.risk_model import estimate_handling_and_risk, estimate_safety_status
from analytics.tire_degradation import estimate_tire_degradation
from analytics.track_evolution import estimate_track_evolution


def _clamp(value: float, low: float, high: float) -> float:
	return max(low, min(high, value))


def _to_float(value: Any, default: float) -> float:
	try:
		return float(value)
	except (TypeError, ValueError):
		return default


def _normalized_weather(value: str) -> str:
	weather = value.strip().lower() if value else "unknown"
	if weather in {"clear", "cloudy", "light_rain", "heavy_rain", "mixed", "unknown"}:
		return weather
	return "unknown"


def _normalized_tire_compound(value: str) -> str:
	compound = value.strip().lower() if value else "unknown"
	if compound in {"soft", "medium", "hard", "intermediate", "wet", "unknown"}:
		return compound
	return "unknown"


def build_race_state_from_sensor_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
	"""Build full RaceState model payload from a live telemetry sensor snapshot."""
	car = snapshot.get("car", {})
	driver = snapshot.get("driver", {})
	environment = snapshot.get("environment", {})
	race = snapshot.get("race", {})

	current_segment_id = str(car.get("current_segment_id", race.get("current_segment_id", "unknown_segment")))
	race_lap = int(max(0, race.get("lap_number", car.get("lap_number", 0))))
	total_laps = int(max(1, race.get("total_laps", 58)))

	recommended_speed = float(car.get("recommended_speed_kph", max(100.0, float(car.get("speed_kph", 210.0)) - 8.0)))
	actual_speed = float(car.get("speed_kph", 210.0))
	steering_angle = float(car.get("steering_angle_deg", 0.0))
	brake_pct = float(car.get("brake_pct", 0.0))

	car_state = {
		"speed_kph": max(0.0, actual_speed),
		"gear": int(max(0, car.get("gear", 6))),
		"rpm": max(0.0, float(car.get("rpm", 10200))),
		"throttle_pct": _clamp(float(car.get("throttle_pct", 72.0)), 0.0, 100.0),
		"brake_pct": _clamp(brake_pct, 0.0, 100.0),
		"steering_angle_deg": steering_angle,
		"lap_number": race_lap,
		"distance_on_lap_m": max(0.0, float(car.get("distance_on_lap_m", 0.0))),
		"current_segment_id": current_segment_id,
		"tire_compound": _normalized_tire_compound(str(car.get("tire_compound", "unknown"))),
		"tire_wear_pct": _clamp(float(car.get("tire_wear_pct", 20.0)), 0.0, 100.0),
		"tire_temp_c": float(car.get("tire_temp_c", 95.0)),
		"fuel_remaining_l": max(0.0, float(car.get("fuel_remaining_l", 40.0))),
		"brake_temp_c": float(car.get("brake_temp_c", 580.0)),
		"suspension_load_front": float(car.get("suspension_load_front", 0.8)),
		"suspension_load_rear": float(car.get("suspension_load_rear", 0.78)),
	}

	environment_state = {
		"ambient_temp_c": float(environment.get("ambient_temp_c", 27.0)),
		"track_temp_c_estimate": float(environment.get("track_temp_c_estimate", 36.5)),
		"weather_condition": _normalized_weather(str(environment.get("weather_condition", "unknown"))),
		"wind_speed_kph": max(0.0, float(environment.get("wind_speed_kph", 11.0))),
		"wind_direction_deg": _clamp(float(environment.get("wind_direction_deg", 180.0)), 0.0, 360.0),
		"grip_factor": max(0.0, float(environment.get("grip_factor", 1.0))),
	}

	race_context = {
		"race_lap": race_lap,
		"total_laps": total_laps,
		"position_overall": int(max(1, race.get("position_overall", 8))),
		"gap_ahead_s": max(0.0, float(race.get("gap_ahead_s", 2.3))),
		"gap_behind_s": max(0.0, float(race.get("gap_behind_s", 1.9))),
		"safety_car_active": bool(race.get("safety_car_active", False)),
		"vsc_active": bool(race.get("vsc_active", False)),
		"yellow_flag_sectors": list(race.get("yellow_flag_sectors", [])),
		"cars_ahead": int(max(0, race.get("cars_ahead", 1))),
		"cars_behind": int(max(0, race.get("cars_behind", 1))),
	}

	driver_state = estimate_driver_state(
		{
			"car": car_state,
			"driver": driver,
			"environment": environment_state,
		}
	)
	driver_override_state = estimate_driver_override(
		actual_speed_kph=actual_speed,
		recommended_speed_kph=recommended_speed,
		steering_angle_deg=steering_angle,
		brake_pct=brake_pct,
	)
	handling_and_risk = estimate_handling_and_risk(
		{
			"car": car_state,
			"driver": driver_state,
			"environment": environment_state,
		},
		override_risk_multiplier=_to_float(driver_override_state.get("override_risk_multiplier"), 1.0),
	)
	tire_degradation = estimate_tire_degradation(
		{
			"car": car_state,
			"environment": environment_state,
		},
		race_lap=race_lap,
	)
	track_evolution = estimate_track_evolution({"environment": environment_state}, race_lap=race_lap)
	fatigue_hydration = estimate_fatigue_hydration(race_lap=race_lap, driver_state=driver_state)
	traffic_model = estimate_traffic_model(snapshot, current_segment_id=current_segment_id)
	safety_status = estimate_safety_status(
		race_context=race_context,
		handling_and_risk=handling_and_risk,
		traffic_model=traffic_model,
		override_model=driver_override_state,
	)
	pit_strategy_model = estimate_pit_strategy(
		race_lap=race_lap,
		total_laps=total_laps,
		tire_degradation=tire_degradation,
		safety_status=safety_status,
		race_context=race_context,
	)
	outcome_projection = estimate_outcome_projection(
		race_context=race_context,
		handling_and_risk=handling_and_risk,
		pit_strategy=pit_strategy_model,
	)

	return {
		"car_state": car_state,
		"driver_state": driver_state,
		"environment_state": environment_state,
		"race_context": race_context,
		"driver_override_state": driver_override_state,
		"handling_and_risk": handling_and_risk,
		"tire_degradation": tire_degradation,
		"track_evolution": track_evolution,
		"fatigue_hydration": fatigue_hydration,
		"traffic_model": traffic_model,
		"safety_status": safety_status,
		"pit_strategy_model": pit_strategy_model,
		"outcome_projection": outcome_projection,
	}
