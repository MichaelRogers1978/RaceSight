from __future__ import annotations

from typing import Any


def _clamp(value: float, low: float, high: float) -> float:
	return max(low, min(high, value))


def estimate_driver_state(snapshot: dict[str, Any]) -> dict[str, Any]:
	"""Build DriverState from live telemetry snapshot fields."""
	driver = snapshot.get("driver", {})
	car = snapshot.get("car", {})

	fatigue = float(driver.get("fatigue_level", 35.0))
	hydration = float(driver.get("hydration_level", 70.0))
	stress = float(driver.get("stress_index", 45.0))
	steering_smoothness = float(driver.get("steering_smoothness", 78.0))
	error_rate = float(driver.get("error_rate", 0.06))

	speed = float(car.get("speed_kph", 210.0))
	reaction_time = float(driver.get("reaction_time_ms_estimate", 215.0 + max(0.0, speed - 180.0) * 0.18))

	style = str(driver.get("driver_style_profile", "balanced")).strip().lower()
	if style not in {"aggressive", "balanced", "conservative", "unknown"}:
		style = "unknown"

	return {
		"fatigue_level": _clamp(fatigue, 0.0, 100.0),
		"hydration_level": _clamp(hydration, 0.0, 100.0),
		"stress_index": _clamp(stress, 0.0, 100.0),
		"reaction_time_ms_estimate": max(0.0, reaction_time),
		"steering_smoothness": _clamp(steering_smoothness, 0.0, 100.0),
		"error_rate": _clamp(error_rate, 0.0, 1.0),
		"driver_style_profile": style,
	}


def estimate_fatigue_hydration(
	race_lap: int,
	driver_state: dict[str, Any],
) -> dict[str, Any]:
	fatigue_level = float(driver_state["fatigue_level"])
	hydration_level = float(driver_state["hydration_level"])

	fatigue_trend = _clamp(0.65 + fatigue_level / 140.0, 0.1, 2.4)
	hydration_trend = -_clamp(0.45 + (100.0 - hydration_level) / 170.0, 0.1, 2.0)

	projected_fatigue_threshold = race_lap + max(0.0, (80.0 - fatigue_level) / max(fatigue_trend, 0.01))
	projected_hydration_critical = race_lap + max(
		0.0,
		(hydration_level - 30.0) / max(abs(hydration_trend), 0.01),
	)

	return {
		"fatigue_trend_per_lap": fatigue_trend,
		"hydration_trend_per_lap": hydration_trend,
		"projected_fatigue_threshold_lap": max(float(race_lap), projected_fatigue_threshold),
		"projected_hydration_critical_lap": max(float(race_lap), projected_hydration_critical),
	}
