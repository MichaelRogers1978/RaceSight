from __future__ import annotations

from typing import Any


def _clamp(value: float, low: float, high: float) -> float:
	return max(low, min(high, value))


def estimate_tire_degradation(
	snapshot: dict[str, Any],
	race_lap: int,
) -> dict[str, Any]:
	car = snapshot.get("car", {})
	environment = snapshot.get("environment", {})

	tire_wear = float(car.get("tire_wear_pct", 25.0))
	tire_temp = float(car.get("tire_temp_c", 94.0))
	track_temp = float(environment.get("track_temp_c_estimate", 35.0))

	thermal_penalty = max(0.0, tire_temp - 100.0) * 0.015
	track_penalty = max(0.0, track_temp - 38.0) * 0.008
	wear_rate = _clamp(1.1 + tire_wear / 60.0 + thermal_penalty + track_penalty, 0.5, 4.5)

	remaining_to_cliff = max(0.0, 82.0 - tire_wear)
	laps_to_cliff = remaining_to_cliff / max(wear_rate, 0.01)
	projected_drop = _clamp((100.0 - max(0.0, 82.0 - tire_wear)) * 0.17, 0.0, 100.0)

	pit_start = max(1, int(race_lap + max(0.0, laps_to_cliff - 3.0)))
	pit_end = max(pit_start, int(race_lap + max(0.0, laps_to_cliff - 1.0)))

	return {
		"wear_rate_per_lap_estimate": wear_rate,
		"projected_laps_to_cliff": max(0.0, laps_to_cliff),
		"projected_grip_drop_pct": projected_drop,
		"recommended_pit_window_from_tires": {
			"start_lap": pit_start,
			"end_lap": pit_end,
		},
	}
