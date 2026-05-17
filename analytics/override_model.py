from __future__ import annotations


def estimate_driver_override(
	actual_speed_kph: float,
	recommended_speed_kph: float,
	steering_angle_deg: float,
	brake_pct: float,
) -> dict[str, object]:
	speed_delta = actual_speed_kph - recommended_speed_kph
	override_detected = speed_delta > 6.0 or (abs(steering_angle_deg) > 16.0 and brake_pct < 8.0)

	if speed_delta > 12.0:
		override_type = "speeding"
	elif brake_pct < 6.0 and speed_delta > 5.0:
		override_type = "late_braking"
	elif abs(steering_angle_deg) > 18.0:
		override_type = "line_deviation"
	else:
		override_type = "none"

	intensity = max(0.0, min(100.0, abs(speed_delta) * 3.5 + abs(steering_angle_deg) * 0.9))
	multiplier = 1.0 + (intensity / 100.0) * 0.6

	return {
		"override_detected": override_detected,
		"override_intensity": intensity,
		"override_type": override_type,
		"recommended_speed_kph": max(0.0, recommended_speed_kph),
		"actual_speed_kph": max(0.0, actual_speed_kph),
		"adjusted_safe_speed_kph": max(0.0, recommended_speed_kph - intensity * 0.08),
		"adjusted_braking_point_m": max(0.0, 95.0 + intensity * 0.3),
		"override_risk_multiplier": multiplier,
		"extra_tire_wear_per_lap": max(0.0, (multiplier - 1.0) * 1.3),
	}
