from __future__ import annotations

from typing import Any


def _clamp(value: float, low: float, high: float) -> float:
	return max(low, min(high, value))


def estimate_traffic_model(snapshot: dict[str, Any], current_segment_id: str) -> dict[str, Any]:
	traffic = snapshot.get("traffic", {})
	slow_gap = float(traffic.get("slow_car_gap_s", 999.0))
	slow_delta = float(traffic.get("slow_car_speed_delta_kph", 0.0))
	overtake_possible = bool(traffic.get("overtake_possible_here", False))
	recommended_segment = traffic.get("recommended_overtake_segment_id") or current_segment_id

	slow_car_ahead = slow_gap <= 3.0 and slow_delta < -1.0
	return {
		"slow_car_ahead": slow_car_ahead,
		"slow_car_gap_s": max(0.0, slow_gap),
		"slow_car_speed_delta_kph": slow_delta,
		"overtake_possible_here": overtake_possible,
		"recommended_overtake_segment_id": str(recommended_segment) if overtake_possible else None,
	}


def estimate_pit_strategy(
	race_lap: int,
	total_laps: int,
	tire_degradation: dict[str, Any],
	safety_status: dict[str, Any],
	race_context: dict[str, Any],
) -> dict[str, Any]:
	window = tire_degradation["recommended_pit_window_from_tires"]
	start_lap = int(window["start_lap"])
	end_lap = int(window["end_lap"])

	safety_car = bool(race_context.get("safety_car_active", False))
	vsc = bool(race_context.get("vsc_active", False))
	risk = float(safety_status.get("alert_level") in {"warning", "critical"})

	should_pit = race_lap >= start_lap or safety_car or vsc
	if race_lap >= total_laps - 2:
		should_pit = False

	confidence = 78.0
	if safety_car or vsc:
		confidence += 9.0
	confidence -= risk * 6.0

	primary_reason = "Tire degradation window open"
	secondary_reason = "Track position can be protected"
	if safety_car:
		primary_reason = "Safety car creates low-loss pit opportunity"
	elif vsc:
		primary_reason = "VSC window reduces pit stop penalty"

	return {
		"should_pit_now": should_pit,
		"recommended_pit_lap_window": {
			"start_lap": start_lap,
			"end_lap": max(start_lap, end_lap),
		},
		"primary_reason": primary_reason,
		"secondary_reason": secondary_reason,
		"actions": [
			{
				"change_tires": True,
				"refuel": False,
				"front_wing_adjustment_clicks": 0,
				"brake_duct_adjustment": 0.0,
				"cooling_adjustment": 0.0,
				"driver_hydration_check": True,
				"driver_change": False,
			}
		],
		"target_pit_time_s": 22.3 if (safety_car or vsc) else 23.9,
		"risk_if_delayed": _clamp(float(tire_degradation["projected_grip_drop_pct"]) * 0.82, 0.0, 100.0),
		"confidence": _clamp(confidence, 0.0, 100.0),
	}


def estimate_outcome_projection(
	race_context: dict[str, Any],
	handling_and_risk: dict[str, Any],
	pit_strategy: dict[str, Any],
) -> dict[str, Any]:
	position = int(race_context.get("position_overall", 10))
	gap_ahead = float(race_context.get("gap_ahead_s", 3.0))
	handling = float(handling_and_risk.get("handling_score", 70.0))
	risk = float(handling_and_risk.get("risk_index", 35.0))

	current = max(1, position)
	aggressive = max(1, position - (1 if handling > 74.0 and gap_ahead < 2.2 else 0))
	conservative = max(1, position + (1 if risk > 58.0 else 0))
	required_lap_time = max(70.0, 92.0 - (handling - 70.0) * 0.08)

	if pit_strategy.get("should_pit_now"):
		label = "balanced"
		summary = "Pit now to protect long-run grip and stabilize finish projection."
	elif risk > 62.0:
		label = "conservative"
		summary = "Stabilize pace to reduce incident probability and secure points."
	else:
		label = "aggressive" if aggressive < current else "hold_position"
		summary = "Push selectively in clean-air sectors to gain position opportunity."

	return {
		"projected_finish_position_current_strategy": current,
		"projected_finish_position_aggressive_strategy": aggressive,
		"projected_finish_position_conservative_strategy": conservative,
		"required_avg_lap_time_for_target_position": required_lap_time,
		"recommended_strategy_label": label,
		"summary_text": summary,
	}
