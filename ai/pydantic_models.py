from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


Percent = float
Timestamp = datetime


class LapWindow(StrictBaseModel):
    start_lap: int = Field(ge=0)
    end_lap: int = Field(ge=0)


class CarState(StrictBaseModel):
    speed_kph: float = Field(ge=0)
    gear: int = Field(ge=0)
    rpm: float = Field(ge=0)
    throttle_pct: Percent = Field(ge=0, le=100)
    brake_pct: Percent = Field(ge=0, le=100)
    steering_angle_deg: float
    lap_number: int = Field(ge=0)
    distance_on_lap_m: float = Field(ge=0)
    current_segment_id: str = Field(min_length=1)
    tire_compound: Literal["soft", "medium", "hard", "intermediate", "wet", "unknown"]
    tire_wear_pct: Percent = Field(ge=0, le=100)
    tire_temp_c: float
    fuel_remaining_l: float = Field(ge=0)
    brake_temp_c: float
    suspension_load_front: float
    suspension_load_rear: float


class DriverState(StrictBaseModel):
    fatigue_level: Percent = Field(ge=0, le=100)
    hydration_level: Percent = Field(ge=0, le=100)
    stress_index: Percent = Field(ge=0, le=100)
    reaction_time_ms_estimate: float = Field(ge=0)
    steering_smoothness: Percent = Field(ge=0, le=100)
    error_rate: float = Field(ge=0, le=1)
    driver_style_profile: Literal["aggressive", "balanced", "conservative", "unknown"]


class EnvironmentState(StrictBaseModel):
    ambient_temp_c: float
    track_temp_c_estimate: float
    weather_condition: Literal["clear", "cloudy", "light_rain", "heavy_rain", "mixed", "unknown"]
    wind_speed_kph: float = Field(ge=0)
    wind_direction_deg: float = Field(ge=0, le=360)
    grip_factor: float = Field(ge=0)


class RaceContext(StrictBaseModel):
    race_lap: int = Field(ge=0)
    total_laps: int = Field(ge=1)
    position_overall: int = Field(ge=1)
    gap_ahead_s: float = Field(ge=0)
    gap_behind_s: float = Field(ge=0)
    safety_car_active: bool
    vsc_active: bool
    yellow_flag_sectors: list[int]
    cars_ahead: int = Field(ge=0)
    cars_behind: int = Field(ge=0)


class DriverOverrideModel(StrictBaseModel):
    override_detected: bool
    override_intensity: Percent = Field(ge=0, le=100)
    override_type: Literal[
        "speeding",
        "late_braking",
        "aggressive_throttle",
        "line_deviation",
        "none",
        "unknown",
    ]
    recommended_speed_kph: float = Field(ge=0)
    actual_speed_kph: float = Field(ge=0)
    adjusted_safe_speed_kph: float = Field(ge=0)
    adjusted_braking_point_m: float = Field(ge=0)
    override_risk_multiplier: float = Field(ge=0)
    extra_tire_wear_per_lap: float = Field(ge=0)


class HandlingAndRiskModel(StrictBaseModel):
    handling_score: Percent = Field(ge=0, le=100)
    risk_index: Percent = Field(ge=0, le=100)
    instability_events: int = Field(ge=0)
    lockups: int = Field(ge=0)
    off_track_events: int = Field(ge=0)


class TireDegradationModel(StrictBaseModel):
    wear_rate_per_lap_estimate: float = Field(ge=0)
    projected_laps_to_cliff: float = Field(ge=0)
    projected_grip_drop_pct: Percent = Field(ge=0, le=100)
    recommended_pit_window_from_tires: LapWindow


class TrackEvolutionModel(StrictBaseModel):
    grip_trend_per_lap: float
    projected_grip_in_n_laps: float = Field(ge=0)
    track_evolution_rate: float


class FatigueHydrationModel(StrictBaseModel):
    fatigue_trend_per_lap: float
    hydration_trend_per_lap: float
    projected_fatigue_threshold_lap: float = Field(ge=0)
    projected_hydration_critical_lap: float = Field(ge=0)


class TrafficModel(StrictBaseModel):
    slow_car_ahead: bool
    slow_car_gap_s: float = Field(ge=0)
    slow_car_speed_delta_kph: float
    overtake_possible_here: bool
    recommended_overtake_segment_id: str | None = Field(default=None, min_length=1)


class SafetyStatus(StrictBaseModel):
    safety_alert_active: bool
    alert_level: Literal["none", "advisory", "warning", "critical"]
    alert_reason: str = Field(min_length=1)
    recommended_action: str = Field(min_length=1)
    enforced_mode: Literal["none", "yellow", "vsc", "safety_car", "pit_limiter", "unknown"]


class PitAction(StrictBaseModel):
    change_tires: bool
    refuel: bool
    front_wing_adjustment_clicks: int
    brake_duct_adjustment: float
    cooling_adjustment: float
    driver_hydration_check: bool
    driver_change: bool


class PitStrategyModel(StrictBaseModel):
    should_pit_now: bool
    recommended_pit_lap_window: LapWindow
    primary_reason: str = Field(min_length=1)
    secondary_reason: str = Field(min_length=1)
    actions: list[PitAction] = Field(min_length=1)
    target_pit_time_s: float = Field(ge=0)
    risk_if_delayed: Percent = Field(ge=0, le=100)
    confidence: Percent = Field(ge=0, le=100)


class OutcomeProjection(StrictBaseModel):
    projected_finish_position_current_strategy: int = Field(ge=1)
    projected_finish_position_aggressive_strategy: int = Field(ge=1)
    projected_finish_position_conservative_strategy: int = Field(ge=1)
    required_avg_lap_time_for_target_position: float = Field(ge=0)
    recommended_strategy_label: Literal[
        "aggressive", "balanced", "conservative", "hold_position", "unknown"
    ]
    summary_text: str = Field(min_length=1)


class RaceState(StrictBaseModel):
    car_state: CarState
    driver_state: DriverState
    environment_state: EnvironmentState
    race_context: RaceContext
    driver_override_state: DriverOverrideModel
    handling_and_risk: HandlingAndRiskModel
    tire_degradation: TireDegradationModel
    track_evolution: TrackEvolutionModel
    fatigue_hydration: FatigueHydrationModel
    traffic_model: TrafficModel
    safety_status: SafetyStatus
    pit_strategy_model: PitStrategyModel
    outcome_projection: OutcomeProjection


class TelemetryPoint(StrictBaseModel):
    timestamp: Timestamp
    car_state: CarState
    driver_state: DriverState
    environment_state: EnvironmentState
    race_context: RaceContext
    segment_id: str = Field(min_length=1)


class RaceEvent(StrictBaseModel):
    timestamp: Timestamp
    lap_number: int = Field(ge=0)
    type: str = Field(min_length=1)
    location_segment_id: str = Field(min_length=1)
    severity: Literal["info", "low", "medium", "high", "critical"]
    description: str = Field(min_length=1)


class GetRaceStateParameters(StrictBaseModel):
    pass


class ComputeDriverCoachingParameters(StrictBaseModel):
    race_state: RaceState


class ComputePitStrategyParameters(StrictBaseModel):
    race_state: RaceState


class EvaluateSafetyStatusParameters(StrictBaseModel):
    race_state: RaceState


class RunWhatIfScenarioParameters(StrictBaseModel):
    race_state: RaceState
    scenario: str = Field(min_length=1)


class GeneratePostRaceSummaryParameters(StrictBaseModel):
    race_log: list[TelemetryPoint | RaceEvent]


class GetRaceStateTool(StrictBaseModel):
    name: Literal["get_race_state"]
    description: Literal[
        "Retrieve the latest unified RaceState snapshot containing car, driver, environment, safety, strategy, and prediction models."
    ]
    parameters: GetRaceStateParameters


class ComputeDriverCoachingTool(StrictBaseModel):
    name: Literal["compute_driver_coaching"]
    description: Literal["Generate turn-by-turn coaching instructions based on the current RaceState."]
    parameters: ComputeDriverCoachingParameters


class ComputePitStrategyTool(StrictBaseModel):
    name: Literal["compute_pit_strategy"]
    description: Literal[
        "Compute optimal pit strategy based on tires, fuel, degradation, race context, and predictive models."
    ]
    parameters: ComputePitStrategyParameters


class EvaluateSafetyStatusTool(StrictBaseModel):
    name: Literal["evaluate_safety_status"]
    description: Literal[
        "Evaluate safety conditions, risk levels, incidents, and compliance based on the current RaceState."
    ]
    parameters: EvaluateSafetyStatusParameters


class RunWhatIfScenarioTool(StrictBaseModel):
    name: Literal["run_what_if_scenario"]
    description: Literal[
        "Simulate an alternative race scenario such as pitting now, staying out, tire changes, or safety car conditions."
    ]
    parameters: RunWhatIfScenarioParameters


class GeneratePostRaceSummaryTool(StrictBaseModel):
    name: Literal["generate_post_race_summary"]
    description: Literal[
        "Generate a structured post-race summary including key moments, strategy evaluation, driver performance, and safety interventions."
    ]
    parameters: GeneratePostRaceSummaryParameters


ToolDefinition = (
    GetRaceStateTool
    | ComputeDriverCoachingTool
    | ComputePitStrategyTool
    | EvaluateSafetyStatusTool
    | RunWhatIfScenarioTool
    | GeneratePostRaceSummaryTool
)


class GraniteToolSchemas(StrictBaseModel):
    tools: list[ToolDefinition] = Field(min_length=6)


class FunctionSpec(StrictBaseModel):
    name: str
    description: str
    parameters: dict


class RuntimeTool(StrictBaseModel):
    type: Literal["function"]
    function: FunctionSpec


class RuntimeToolRegistration(StrictBaseModel):
    tool_choice: Literal["auto"] = "auto"
    tools: list[RuntimeTool] = Field(min_length=1)
