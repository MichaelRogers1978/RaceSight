## RaceSight Data Models ##

This document defines all data structures used throughout the RaceSight system.

## 1. Static Configuration Models ##

TrackModel:
id

name

lap_length_m

segments: list of TrackSegment

TrackSegment:
id

sequence_index

type (straight, corner, chicane, etc.)

sector

length_m

radius_m

elevation_change_m

base_safe_speed_kph

overtake_possible

CarSpec:
car_id

car_mass_kg

power_kw

downforce_level

drag_coefficient

brake_efficiency

fuel_tank_capacity_l

fuel_consumption_l_per_lap

suspension_stiffness

ride_height_mm

aero_balance_front_pct

cooling_efficiency

TireSpec:
compound_name

base_wear_rate_per_lap

optimal_temp_min_c

optimal_temp_max_c

base_grip_factor

degradation_curve_params

warmup_laps

performance_cliff_wear_pct

rain_modifier

track_temp_sensitivity

## 2. Dynamic State Models ##

CarState:
speed_kph

gear

rpm

throttle_pct

brake_pct

steering_angle_deg

lap_number

distance_on_lap_m

current_segment_id

tire_compound

tire_wear_pct

tire_temp_c

fuel_remaining_l

brake_temp_c

suspension_load_front/rear

DriverState:
fatigue_level

hydration_level

stress_index

reaction_time_ms_estimate

steering_smoothness

error_rate

driver_style_profile

EnvironmentState:
ambient_temp_c

track_temp_c_estimate

weather_condition

wind_speed_kph

wind_direction_deg

grip_factor

RaceContext
race_lap

total_laps

position_overall

gap_ahead_s

gap_behind_s

safety_car_active

vsc_active

yellow_flag_sectors

cars_ahead/behind

TelemetryPoint:
timestamp

car_state

driver_state

environment_state

race_context

segment_id

## 3. Behavior & Override Models ##

DriverOverrideModel:
override_detected

override_intensity

override_type

recommended_speed_kph

actual_speed_kph

adjusted_safe_speed_kph

adjusted_braking_point_m

override_risk_multiplier

extra_tire_wear_per_lap

HandlingAndRiskModel:
handling_score

risk_index

instability_events

lockups

off_track_events

## 4. Prediction Models ##

TireDegradationModel:
wear_rate_per_lap_estimate

projected_laps_to_cliff

projected_grip_drop_pct

recommended_pit_window_from_tires

TrackEvolutionModel:
grip_trend_per_lap

projected_grip_in_n_laps

track_evolution_rate

FatigueHydrationModel:
fatigue_trend_per_lap

hydration_trend_per_lap

projected_fatigue_threshold_lap

projected_hydration_critical_lap

LapSummary:
lap_number

lap_time_s

sector_times_s

avg_speed_kph

avg_handling_score

max_risk_index

avg_tire_wear_rate

fatigue_delta

weather_snapshot

## 5. Events & Safety Models ##

RaceEvent:
timestamp

lap_number

type

location_segment_id

severity

description

TrafficModel:
slow_car_ahead

slow_car_gap_s

slow_car_speed_delta_kph

overtake_possible_here

recommended_overtake_segment_id

SafetyStatus:
safety_alert_active

alert_level

alert_reason

recommended_action

enforced_mode

## 6. Strategy & Outcome Models ##

PitAction:
change_tires

refuel

front_wing_adjustment_clicks

brake_duct_adjustment

cooling_adjustment

driver_hydration_check

driver_change

PitStrategyModel:
should_pit_now

recommended_pit_lap_window

primary_reason

secondary_reason

actions

target_pit_time_s

risk_if_delayed

confidence

OutcomeProjection:
projected_finish_position_current_strategy

projected_finish_position_aggressive_strategy

projected_finish_position_conservative_strategy

required_avg_lap_time_for_target_position

recommended_strategy_label

summary_text

## 7. Unified RaceState ##
A single snapshot containing:

car_state

driver_state

environment_state

race_context

driver_override_state

handling_and_risk

tire_degradation

track_evolution

fatigue_hydration

traffic_model

safety_status

pit_strategy_model

outcome_projection

This is the central data object used by all AI agents.

## RaceSight Class Diagram ##

┌──────────────────────────────┐
│          TrackModel          │
├──────────────────────────────┤
│ id                           │
│ name                         │
│ lap_length_m                 │
│ segments: List<TrackSegment> │
└──────────────────────────────┘
                ▲
                │
┌──────────────────────────────┐
│        TrackSegment          │
├──────────────────────────────┤
│ id                           │
│ sequence_index               │
│ type                         │
│ sector                       │
│ length_m                     │
│ radius_m                     │
│ elevation_change_m           │
│ base_safe_speed_kph          │
│ overtake_possible            │
└──────────────────────────────┘


┌──────────────────────────────┐
│           CarSpec            │
├──────────────────────────────┤
│ car_id                       │
│ car_mass_kg                  │
│ power_kw                     │
│ downforce_level              │
│ drag_coefficient             │
│ brake_efficiency             │
│ fuel_tank_capacity_l         │
│ fuel_consumption_l_per_lap   │
│ suspension_stiffness         │
│ ride_height_mm               │
│ aero_balance_front_pct       │
│ cooling_efficiency           │
└──────────────────────────────┘

┌──────────────────────────────┐
│           TireSpec           │
├──────────────────────────────┤
│ compound_name                │
│ base_wear_rate_per_lap       │
│ optimal_temp_min_c           │
│ optimal_temp_max_c           │
│ base_grip_factor             │
│ degradation_curve_params     │
│ warmup_laps                  │
│ performance_cliff_wear_pct   │
│ rain_modifier                │
│ track_temp_sensitivity       │
└──────────────────────────────┘


┌──────────────────────────────┐
│           CarState           │
├──────────────────────────────┤
│ speed_kph                    │
│ gear                         │
│ rpm                          │
│ throttle_pct                 │
│ brake_pct                    │
│ steering_angle_deg           │
│ lap_number                   │
│ distance_on_lap_m            │
│ current_segment_id           │
│ tire_compound                │
│ tire_wear_pct                │
│ tire_temp_c                  │
│ fuel_remaining_l             │
│ brake_temp_c                 │
│ suspension_load_front/rear   │
└──────────────────────────────┘

┌──────────────────────────────┐
│         DriverState          │
├──────────────────────────────┤
│ fatigue_level                │
│ hydration_level              │
│ stress_index                 │
│ reaction_time_ms_estimate    │
│ steering_smoothness          │
│ error_rate                   │
│ driver_style_profile         │
└──────────────────────────────┘

┌──────────────────────────────┐
│       EnvironmentState       │
├──────────────────────────────┤
│ ambient_temp_c               │
│ track_temp_c_estimate        │
│ weather_condition            │
│ wind_speed_kph               │
│ wind_direction_deg           │
│ grip_factor                  │
└──────────────────────────────┘

┌──────────────────────────────┐
│         RaceContext          │
├──────────────────────────────┤
│ race_lap                     │
│ total_laps                   │
│ position_overall             │
│ gap_ahead_s                  │
│ gap_behind_s                 │
│ safety_car_active            │
│ vsc_active                   │
│ yellow_flag_sectors          │
│ cars_ahead/behind            │
└──────────────────────────────┘


┌──────────────────────────────┐
│        TelemetryPoint        │
├──────────────────────────────┤
│ timestamp                    │
│ car_state                    │
│ driver_state                 │
│ environment_state            │
│ race_context                 │
│ segment_id                   │
└──────────────────────────────┘


┌──────────────────────────────┐
│     DriverOverrideModel      │
├──────────────────────────────┤
│ override_detected            │
│ override_intensity           │
│ override_type                │
│ recommended_speed_kph        │
│ actual_speed_kph             │
│ adjusted_safe_speed_kph      │
│ adjusted_braking_point_m     │
│ override_risk_multiplier     │
│ extra_tire_wear_per_lap      │
└──────────────────────────────┘


┌──────────────────────────────┐
│     HandlingAndRiskModel     │
├──────────────────────────────┤
│ handling_score               │
│ risk_index                   │
│ instability_events           │
│ lockups                      │
│ off_track_events             │
└──────────────────────────────┘


┌──────────────────────────────┐
│    TireDegradationModel      │
├──────────────────────────────┤
│ wear_rate_per_lap_estimate   │
│ projected_laps_to_cliff      │
│ projected_grip_drop_pct      │
│ recommended_pit_window       │
└──────────────────────────────┘

┌──────────────────────────────┐
│     TrackEvolutionModel      │
├──────────────────────────────┤
│ grip_trend_per_lap           │
│ projected_grip_in_n_laps     │
│ track_evolution_rate         │
└──────────────────────────────┘

┌──────────────────────────────┐
│    FatigueHydrationModel     │
├──────────────────────────────┤
│ fatigue_trend_per_lap        │
│ hydration_trend_per_lap      │
│ projected_fatigue_threshold  │
│ projected_hydration_critical │
└──────────────────────────────┘


┌──────────────────────────────┐
│          LapSummary          │
├──────────────────────────────┤
│ lap_number                   │
│ lap_time_s                   │
│ sector_times_s               │
│ avg_speed_kph                │
│ avg_handling_score           │
│ max_risk_index               │
│ avg_tire_wear_rate           │
│ fatigue_delta                │
│ weather_snapshot             │
└──────────────────────────────┘


┌──────────────────────────────┐
│          RaceEvent           │
├──────────────────────────────┤
│ timestamp                    │
│ lap_number                   │
│ type                         │
│ location_segment_id          │
│ severity                     │
│ description                  │
└──────────────────────────────┘


┌──────────────────────────────┐
│         TrafficModel         │
├──────────────────────────────┤
│ slow_car_ahead               │
│ slow_car_gap_s               │
│ slow_car_speed_delta_kph     │
│ overtake_possible_here       │
│ recommended_overtake_segment │
└──────────────────────────────┘


┌──────────────────────────────┐
│         SafetyStatus         │
├──────────────────────────────┤
│ safety_alert_active          │
│ alert_level                  │
│ alert_reason                 │
│ recommended_action           │
│ enforced_mode                │
└──────────────────────────────┘


┌──────────────────────────────┐
│          PitAction           │
├──────────────────────────────┤
│ change_tires                 │
│ refuel                       │
│ front_wing_adjustment        │
│ brake_duct_adjustment        │
│ cooling_adjustment           │
│ driver_hydration_check       │
│ driver_change                │
└──────────────────────────────┘


┌──────────────────────────────┐
│       PitStrategyModel       │
├──────────────────────────────┤
│ should_pit_now               │
│ recommended_pit_lap_window   │
│ primary_reason               │
│ secondary_reason             │
│ actions: List<PitAction>     │
│ target_pit_time_s            │
│ risk_if_delayed              │
│ confidence                   │
└──────────────────────────────┘


┌──────────────────────────────┐
│      OutcomeProjection       │
├──────────────────────────────┤
│ projected_finish_current     │
│ projected_finish_aggressive  │
│ projected_finish_conservative│
│ required_avg_lap_time        │
│ recommended_strategy_label   │
│ summary_text                 │
└──────────────────────────────┘


┌──────────────────────────────┐
│           RaceState          │
├──────────────────────────────┤
│ car_state                    │
│ driver_state                 │
│ environment_state            │
│ race_context                 │
│ driver_override_state        │
│ handling_and_risk            │
│ tire_degradation             │
│ track_evolution              │
│ fatigue_hydration            │
│ traffic_model                │
│ safety_status                │
│ pit_strategy_model           │
│ outcome_projection           │
└──────────────────────────────┘

## Safety System State Machine ##

┌───────────────────────────────────────────────────────────────┐
│                    Safety System State Machine                │
└───────────────────────────────────────────────────────────────┘

States:
  • NORMAL
  • CAUTION
  • INCIDENT_REVIEW
  • SAFETY_CAR_ACTIVE
  • VSC_ACTIVE
  • RED_FLAG

Events / Inputs:
  • risk_low / risk_medium / risk_high
  • yellow_flag_sector
  • incident_detected
  • multi_car_incident
  • debris_on_track
  • race_control_safety_car
  • race_control_vsc
  • race_control_red_flag
  • track_clear
  • safety_car_in
  • vsc_ended

---------------------------------------------------------------

          ┌──────────┐
          │  NORMAL  │
          └────┬─────┘
     risk_high │
 incident_detected
              ▼
        ┌───────────────┐
        │   CAUTION     │  (e.g., local yellow, elevated risk)
        └────┬─────┬────┘
             │     │
             │     │ multi_car_incident
             │     │ debris_on_track
             │     ▼
             │  ┌───────────────┐
             │  │ INCIDENT_     │
             │  │  REVIEW       │
             │  └────┬─────┬────┘
             │       │     │
             │       │     │ race_control_safety_car
             │       │     ▼
             │       │  ┌───────────────┐
             │       │  │ SAFETY_CAR_   │
             │       │  │   ACTIVE      │
             │       │  └────┬─────┬────┘
             │       │       │     │
             │       │ track_clear │ safety_car_in
             │       │       │     ▼
             │       │       │  ┌──────────┐
             │       │       │  │ NORMAL   │
             │       │       │  └──────────┘
             │       │       │
             │       │       │ race_control_red_flag
             │       │       ▼
             │       │  ┌───────────────┐
             │       │  │   RED_FLAG    │
             │       │  └───────────────┘
             │       │
             │       │ race_control_vsc
             │       ▼
             │   ┌───────────────┐
             │   │  VSC_ACTIVE   │
             │   └────┬─────┬────┘
             │        │     │
             │        │ vsc_ended
             │        ▼
             │    ┌──────────┐
             └────│  NORMAL  │
                  └──────────┘

From any state:
  • race_control_red_flag → RED_FLAG
  • track_clear & risk_low → NORMAL

## Driver Override State Machine ##

┌───────────────────────────────────────────────────────────────┐
│                 Driver Override State Machine                 │
└───────────────────────────────────────────────────────────────┘

States:
  • NORMAL_CONTROL
  • MINOR_OVERRIDE
  • MAJOR_OVERRIDE
  • CRITICAL_OVERRIDE
  • RECOVERY

Inputs:
  • speed_delta (actual - recommended)
  • braking_aggression
  • steering_aggression
  • risk_index
  • fatigue_level
  • override_duration
  • track_condition_change

---------------------------------------------------------------

                ┌────────────────────┐
                │  NORMAL_CONTROL    │
                └─────────┬──────────┘
                          │ speed_delta > threshold_low
                          ▼
                ┌────────────────────┐
                │  MINOR_OVERRIDE    │
                └───────┬─────┬──────┘
                        │     │ override_duration > t_med
                        │     ▼
                        │  ┌────────────────────┐
                        │  │  MAJOR_OVERRIDE    │
                        │  └───────┬─────┬──────┘
                        │          │     │ risk_index > high
                        │          │     ▼
                        │          │  ┌────────────────────┐
                        │          │  │ CRITICAL_OVERRIDE  │
                        │          │  └───────┬────────────┘
                        │          │          │
                        │          │          │ driver reduces aggression
                        │          │          ▼
                        │          │   ┌──────────────┐
                        │          └─▶│   RECOVERY    │
                        │              └───────┬───────┘
                        │                      │
                        │ track_condition_change│
                        ▼                      ▼
                ┌────────────────────┐   ┌──────────────┐
                │  NORMAL_CONTROL    │◀─│   NORMAL      │
                └────────────────────┘   └──────────────┘

Transitions from any state:
  • sudden_rain / grip_loss → MAJOR_OVERRIDE
  • safety_alert → CRITICAL_OVERRIDE

## Pit Strategy State Machine ##

┌───────────────────────────────────────────────────────────────┐
│                 Pit Strategy State Machine                    │
└───────────────────────────────────────────────────────────────┘

States:
  • NO_STOP
  • ONE_STOP
  • TWO_STOP
  • SAFETY_WINDOW
  • EMERGENCY_PIT
  • FINISH_MODE

Inputs:
  • tire_wear_pct
  • fuel_remaining_l
  • degradation_rate
  • safety_car_active
  • vsc_active
  • incident_ahead
  • lap_number
  • projected_finish_gain
  • risk_index
  • weather_change

---------------------------------------------------------------

                    ┌───────────────┐
                    │   NO_STOP     │
                    └──────┬────────┘
                           │ tire_wear_pct > threshold
                           ▼
                    ┌───────────────┐
                    │   ONE_STOP    │
                    └──────┬────────┘
                           │ degradation_rate > high
                           ▼
                    ┌───────────────┐
                    │   TWO_STOP    │
                    └──────┬────────┘
                           │ safety_car_active
                           ▼
                    ┌──────────────────┐
                    │  SAFETY_WINDOW   │
                    └──────┬───────────┘
                           │ fuel_critical OR tire_cliff
                           ▼
                    ┌──────────────────┐
                    │  EMERGENCY_PIT   │
                    └──────┬───────────┘
                           │ pit_completed
                           ▼
                    ┌───────────────┐
                    │  FINISH_MODE  │
                    └───────────────┘

Transitions from any state:
  • race_control_red_flag → FINISH_MODE
  • weather_change → ONE_STOP or TWO_STOP (depending on compound)
  • projected_finish_gain > threshold → move to more aggressive strategy
