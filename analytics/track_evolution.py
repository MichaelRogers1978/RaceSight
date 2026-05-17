from __future__ import annotations

from typing import Any


def estimate_track_evolution(snapshot: dict[str, Any], race_lap: int) -> dict[str, Any]:
	environment = snapshot.get("environment", {})
	grip = float(environment.get("grip_factor", 1.0))
	weather = str(environment.get("weather_condition", "clear")).lower()

	weather_modifier = {
		"clear": 0.004,
		"cloudy": 0.002,
		"mixed": -0.001,
		"light_rain": -0.004,
		"heavy_rain": -0.009,
	}.get(weather, 0.0)

	lap_modifier = 0.00015 * min(max(race_lap, 0), 60)
	trend = weather_modifier + lap_modifier
	projected = max(0.7, grip + trend * 6.0)

	return {
		"grip_trend_per_lap": trend,
		"projected_grip_in_n_laps": projected,
		"track_evolution_rate": trend,
	}
