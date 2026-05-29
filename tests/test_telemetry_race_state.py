from __future__ import annotations

import json

import pytest

from core.race_state import build_race_state_from_sensor_snapshot
from core.telemetry import TelemetryFeedError, load_sensor_snapshot


def test_load_sensor_snapshot_from_file(tmp_path) -> None:
    payload = {
        "car": {"speed_kph": 220.0, "lap_number": 10},
        "race": {"lap_number": 10, "total_laps": 58},
    }
    feed = tmp_path / "feed.json"
    feed.write_text(json.dumps(payload), encoding="utf-8")

    loaded = load_sensor_snapshot(source_file=feed)

    assert loaded["car"]["speed_kph"] == 220.0
    assert loaded["race"]["lap_number"] == 10


def test_load_sensor_snapshot_missing_required_keys(tmp_path) -> None:
    feed = tmp_path / "feed.json"
    feed.write_text(json.dumps({"car": {}}), encoding="utf-8")

    with pytest.raises(TelemetryFeedError):
        load_sensor_snapshot(source_file=feed)


def test_build_race_state_has_expected_sections() -> None:
    snapshot = {
        "car": {
            "speed_kph": 236.4,
            "gear": 7,
            "rpm": 11180,
            "throttle_pct": 84.0,
            "brake_pct": 2.0,
            "steering_angle_deg": -1.8,
            "lap_number": 22,
            "distance_on_lap_m": 3630.4,
            "current_segment_id": "s3_t2",
            "tire_compound": "medium",
            "tire_wear_pct": 48.2,
            "tire_temp_c": 99.1,
            "fuel_remaining_l": 28.4,
            "brake_temp_c": 624.0,
            "suspension_load_front": 0.82,
            "suspension_load_rear": 0.78,
            "recommended_speed_kph": 228.0,
        },
        "driver": {
            "fatigue_level": 46.0,
            "hydration_level": 61.0,
            "stress_index": 56.0,
            "reaction_time_ms_estimate": 229.0,
            "steering_smoothness": 74.0,
            "error_rate": 0.09,
            "driver_style_profile": "balanced",
        },
        "environment": {
            "ambient_temp_c": 30.2,
            "track_temp_c_estimate": 39.4,
            "weather_condition": "clear",
            "wind_speed_kph": 14.0,
            "wind_direction_deg": 196.0,
            "grip_factor": 1.01,
        },
        "race": {
            "lap_number": 22,
            "total_laps": 58,
            "position_overall": 7,
            "gap_ahead_s": 1.36,
            "gap_behind_s": 0.92,
            "safety_car_active": False,
            "vsc_active": False,
            "yellow_flag_sectors": [],
            "cars_ahead": 1,
            "cars_behind": 1,
        },
        "traffic": {
            "slow_car_gap_s": 1.36,
            "slow_car_speed_delta_kph": -6.0,
            "overtake_possible_here": True,
            "recommended_overtake_segment_id": "s3_t3",
        },
    }

    race_state = build_race_state_from_sensor_snapshot(snapshot)

    for key in {
        "car_state",
        "driver_state",
        "environment_state",
        "race_context",
        "driver_override_state",
        "handling_and_risk",
        "tire_degradation",
        "track_evolution",
        "fatigue_hydration",
        "traffic_model",
        "safety_status",
        "pit_strategy_model",
        "outcome_projection",
    }:
        assert key in race_state
