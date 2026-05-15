from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from pydantic import ValidationError

try:
    from .pydantic_models import (
        ComputeDriverCoachingParameters,
        ComputePitStrategyParameters,
        EvaluateSafetyStatusParameters,
        GeneratePostRaceSummaryParameters,
        GetRaceStateParameters,
        RaceState,
        RunWhatIfScenarioParameters,
        RuntimeToolRegistration,
    )
except ImportError:
    from pydantic_models import (
        ComputeDriverCoachingParameters,
        ComputePitStrategyParameters,
        EvaluateSafetyStatusParameters,
        GeneratePostRaceSummaryParameters,
        GetRaceStateParameters,
        RaceState,
        RunWhatIfScenarioParameters,
        RuntimeToolRegistration,
    )


STRICT_RUNTIME_FILE = "granite_tool_registration.runtime.strict.json"

## Tools that require a RaceState payload at runtime ##
RACE_STATE_TOOLS = {
    "compute_driver_coaching",
    "compute_pit_strategy",
    "evaluate_safety_status",
    "run_what_if_scenario",
}

TOOL_PARAMETER_MODELS = {
    "get_race_state": GetRaceStateParameters,
    "compute_driver_coaching": ComputeDriverCoachingParameters,
    "compute_pit_strategy": ComputePitStrategyParameters,
    "evaluate_safety_status": EvaluateSafetyStatusParameters,
    "run_what_if_scenario": RunWhatIfScenarioParameters,
    "generate_post_race_summary": GeneratePostRaceSummaryParameters,
}

ToolExecutor = Callable[[dict[str, Any]], Any]


def load_runtime_registration(
    runtime_json_path: str | Path | None = None,
) -> RuntimeToolRegistration:
    """Load and validate the strict Granite runtime registration file."""
    base_dir = Path(__file__).resolve().parent
    target = Path(runtime_json_path) if runtime_json_path else base_dir / STRICT_RUNTIME_FILE

    with target.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return RuntimeToolRegistration.model_validate(data)


def validate_race_state_payload(payload: dict[str, Any]) -> RaceState:
    """Validate a RaceState payload and return the parsed model."""
    return RaceState.model_validate(payload)


def validate_tool_invocation(
    tool_name: str,
    payload: dict[str, Any],
) -> RaceState | None:
    """Validate payload requirements prior to tool execution.

    Returns:
        RaceState model for tools that require it, otherwise None.
    """
    if tool_name in RACE_STATE_TOOLS:
        if "race_state" not in payload:
            raise ValueError(f"Tool '{tool_name}' requires 'race_state' in payload")
        if not isinstance(payload["race_state"], dict):
            raise TypeError("'race_state' must be an object/dict")
        return validate_race_state_payload(payload["race_state"])

    if tool_name == "generate_post_race_summary":
        race_log = payload.get("race_log")
        if not isinstance(race_log, list):
            raise TypeError("'race_log' must be a list")

    if tool_name == "get_race_state" and payload:
        raise ValueError("'get_race_state' does not accept any payload fields")

    return None


def validate_tool_parameters(tool_name: str, payload: dict[str, Any]) -> Any:
    """Validate a tool payload against its exact parameter model class.

    This is the strict typed entry point to use before tool execution.
    """
    parameter_model = TOOL_PARAMETER_MODELS.get(tool_name)
    if parameter_model is None:
        raise ValueError(f"Unknown tool name: {tool_name}")

    return parameter_model.model_validate(payload)


def invoke_tool_with_validation(
    tool_name: str,
    payload: dict[str, Any],
    executors: dict[str, ToolExecutor],
) -> Any:
    """Validate tool payload using exact parameter model, then execute tool handler."""
    validated = validate_tool_parameters(tool_name, payload)

    handler = executors.get(tool_name)
    if handler is None:
        raise ValueError(f"No executor registered for tool: {tool_name}")

    return handler(validated.model_dump())


def invoke_get_race_state(payload: dict[str, Any], executors: dict[str, ToolExecutor]) -> Any:
    return invoke_tool_with_validation("get_race_state", payload, executors)


def invoke_compute_driver_coaching(
    payload: dict[str, Any],
    executors: dict[str, ToolExecutor],
) -> Any:
    return invoke_tool_with_validation("compute_driver_coaching", payload, executors)


def invoke_compute_pit_strategy(
    payload: dict[str, Any],
    executors: dict[str, ToolExecutor],
) -> Any:
    return invoke_tool_with_validation("compute_pit_strategy", payload, executors)


def invoke_evaluate_safety_status(
    payload: dict[str, Any],
    executors: dict[str, ToolExecutor],
) -> Any:
    return invoke_tool_with_validation("evaluate_safety_status", payload, executors)


def invoke_run_what_if_scenario(
    payload: dict[str, Any],
    executors: dict[str, ToolExecutor],
) -> Any:
    return invoke_tool_with_validation("run_what_if_scenario", payload, executors)


def invoke_generate_post_race_summary(
    payload: dict[str, Any],
    executors: dict[str, ToolExecutor],
) -> Any:
    return invoke_tool_with_validation("generate_post_race_summary", payload, executors)


def example_race_state_payload() -> dict[str, Any]:
    """Return a schema-conformant RaceState payload example for testing."""
    return {
        "car_state": {
            "speed_kph": 242.5,
            "gear": 7,
            "rpm": 11250,
            "throttle_pct": 88,
            "brake_pct": 0,
            "steering_angle_deg": -2.4,
            "lap_number": 18,
            "distance_on_lap_m": 3412.7,
            "current_segment_id": "s2_t10",
            "tire_compound": "medium",
            "tire_wear_pct": 46.2,
            "tire_temp_c": 97.4,
            "fuel_remaining_l": 33.1,
            "brake_temp_c": 612.3,
            "suspension_load_front": 0.83,
            "suspension_load_rear": 0.79,
        },
        "driver_state": {
            "fatigue_level": 41.0,
            "hydration_level": 64.0,
            "stress_index": 58.0,
            "reaction_time_ms_estimate": 231,
            "steering_smoothness": 76.5,
            "error_rate": 0.08,
            "driver_style_profile": "balanced",
        },
        "environment_state": {
            "ambient_temp_c": 29.4,
            "track_temp_c_estimate": 38.9,
            "weather_condition": "clear",
            "wind_speed_kph": 13.2,
            "wind_direction_deg": 188,
            "grip_factor": 1.02,
        },
        "race_context": {
            "race_lap": 18,
            "total_laps": 58,
            "position_overall": 6,
            "gap_ahead_s": 1.42,
            "gap_behind_s": 0.87,
            "safety_car_active": False,
            "vsc_active": False,
            "yellow_flag_sectors": [],
            "cars_ahead": 1,
            "cars_behind": 1,
        },
        "driver_override_state": {
            "override_detected": False,
            "override_intensity": 0,
            "override_type": "none",
            "recommended_speed_kph": 238,
            "actual_speed_kph": 242.5,
            "adjusted_safe_speed_kph": 235,
            "adjusted_braking_point_m": 104,
            "override_risk_multiplier": 1.05,
            "extra_tire_wear_per_lap": 0.08,
        },
        "handling_and_risk": {
            "handling_score": 84.2,
            "risk_index": 26.8,
            "instability_events": 0,
            "lockups": 0,
            "off_track_events": 0,
        },
        "tire_degradation": {
            "wear_rate_per_lap_estimate": 1.82,
            "projected_laps_to_cliff": 9.5,
            "projected_grip_drop_pct": 14.7,
            "recommended_pit_window_from_tires": {
                "start_lap": 24,
                "end_lap": 27,
            },
        },
        "track_evolution": {
            "grip_trend_per_lap": 0.006,
            "projected_grip_in_n_laps": 1.05,
            "track_evolution_rate": 0.004,
        },
        "fatigue_hydration": {
            "fatigue_trend_per_lap": 1.1,
            "hydration_trend_per_lap": -0.9,
            "projected_fatigue_threshold_lap": 39,
            "projected_hydration_critical_lap": 46,
        },
        "traffic_model": {
            "slow_car_ahead": True,
            "slow_car_gap_s": 1.42,
            "slow_car_speed_delta_kph": -7.2,
            "overtake_possible_here": True,
            "recommended_overtake_segment_id": "s3_t1",
        },
        "safety_status": {
            "safety_alert_active": False,
            "alert_level": "none",
            "alert_reason": "No active hazards",
            "recommended_action": "Maintain target pace",
            "enforced_mode": "none",
        },
        "pit_strategy_model": {
            "should_pit_now": False,
            "recommended_pit_lap_window": {
                "start_lap": 24,
                "end_lap": 27,
            },
            "primary_reason": "Tire life remains acceptable",
            "secondary_reason": "Track position stable",
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
            "target_pit_time_s": 22.6,
            "risk_if_delayed": 28.4,
            "confidence": 81.0,
        },
        "outcome_projection": {
            "projected_finish_position_current_strategy": 6,
            "projected_finish_position_aggressive_strategy": 5,
            "projected_finish_position_conservative_strategy": 7,
            "required_avg_lap_time_for_target_position": 91.84,
            "recommended_strategy_label": "balanced",
            "summary_text": "Maintain pace and pit in projected window.",
        },
    }


def example_invalid_race_state_payload() -> dict[str, Any]:
    """Return an intentionally invalid RaceState payload for test coverage."""
    bad = example_race_state_payload()
    bad["car_state"]["throttle_pct"] = 150
    bad["driver_state"]["error_rate"] = 1.7
    bad["race_context"]["position_overall"] = 0
    return bad


def example_pre_tool_execution_check() -> None:
    """Small end-to-end example for runtime validation flow."""
    registration = load_runtime_registration()
    print(f"Loaded {len(registration.tools)} registered tools")

    valid_payload = {"race_state": example_race_state_payload()}
    validate_tool_invocation("compute_driver_coaching", valid_payload)
    validate_tool_parameters("compute_driver_coaching", valid_payload)
    print("Valid payload accepted")

    invalid_payload = {"race_state": example_invalid_race_state_payload()}
    try:
        validate_tool_invocation("compute_driver_coaching", invalid_payload)
    except ValidationError as exc:
        print("Invalid payload rejected:")
        print(exc)

    ## Demonstrate call-path wiring: all invocations go through the validated dispatcher ##
    executors: dict[str, ToolExecutor] = {
        "compute_driver_coaching": lambda p: {
            "tool": "compute_driver_coaching",
            "status": "ok",
            "input_keys": sorted(p.keys()),
        }
    }
    dispatch_result = invoke_compute_driver_coaching(valid_payload, executors)
    print(f"Dispatch result: {dispatch_result}")


if __name__ == "__main__":
    example_pre_tool_execution_check()
