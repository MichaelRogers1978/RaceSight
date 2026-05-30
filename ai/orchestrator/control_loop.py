from __future__ import annotations

import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable

from ai.copilot_driver import compute_driver_coaching_adapter
from ai.granite_orchestrator_loader import send_to_granite
from ai.pit_boss import compute_pit_strategy_adapter
from ai.schema_usage import example_race_state_payload
from ai.safety_ai import evaluate_safety_status_adapter
from core.race_state import build_race_state_from_sensor_snapshot
from core.telemetry import TelemetrySeriesError, load_telemetry_series, load_sensor_snapshot


_ORCHESTRATOR_MODULE: ModuleType | None = None


def _load_orchestrator_module() -> ModuleType:
	global _ORCHESTRATOR_MODULE
	if _ORCHESTRATOR_MODULE is not None:
		return _ORCHESTRATOR_MODULE

	workspace_root = Path(__file__).resolve().parents[2]
	orchestrator_path = workspace_root / "main.py" / "orchestrator_main.py"
	spec = importlib.util.spec_from_file_location("racesight_orchestrator_main", orchestrator_path)
	if spec is None or spec.loader is None:
		raise RuntimeError(f"Unable to load orchestrator module from {orchestrator_path}")

	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	_ORCHESTRATOR_MODULE = module
	return module


def racesight_orchestrator(message: str) -> str:
	"""Run the RaceSight orchestration loop for a single user message."""
	module = _load_orchestrator_module()
	orchestrator = getattr(module, "racesight_orchestrator", None)
	if orchestrator is None:
		raise RuntimeError("racesight_orchestrator function is not available in orchestrator_main")
	return orchestrator(message)


def get_race_state() -> dict[str, Any]:
	"""Return the latest telemetry-derived RaceState with a safe fallback."""
	try:
		snapshot = load_sensor_snapshot()
		return build_race_state_from_sensor_snapshot(snapshot)
	except Exception:
		return example_race_state_payload()


def get_runtime_status() -> dict[str, Any]:
	race_state = get_race_state()
	race_context = race_state.get("race_context", {})
	safety_status = race_state.get("safety_status", {})
	pit_strategy = race_state.get("pit_strategy_model", {})
	driver_state = race_state.get("driver_state", {})

	return {
		"status": "online",
		"generated_at": datetime.now(timezone.utc).isoformat(),
		"summary": _summarize_race_state(race_state),
		"race_lap": race_context.get("race_lap"),
		"position": race_context.get("position_overall"),
		"alert_level": safety_status.get("alert_level", "unknown"),
		"pit_now": pit_strategy.get("should_pit_now", False),
		"fatigue_level": driver_state.get("fatigue_level", "n/a"),
	}


def _summarize_race_state(race_state: dict[str, Any]) -> str:
	race_context = race_state.get("race_context", {})
	car_state = race_state.get("car_state", {})
	driver_state = race_state.get("driver_state", {})
	safety_status = race_state.get("safety_status", {})
	pit_strategy = race_state.get("pit_strategy_model", {})

	def _safe_float(value: Any, default: float = 0.0) -> float:
		try:
			return float(value)
		except (TypeError, ValueError):
			return default

	position = race_context.get("position_overall", "n/a")
	lap = race_context.get("race_lap", car_state.get("lap_number", "n/a"))
	gap_ahead = _safe_float(race_context.get("gap_ahead_s", 0.0))
	status = safety_status.get("alert_level", "none")
	should_pit = pit_strategy.get("should_pit_now", False)
	fatigue = driver_state.get("fatigue_level", "n/a")

	return (
		f"Lap {lap}, P{position}, gap ahead {gap_ahead:.2f}s, "
		f"safety={status}, pit_now={should_pit}, fatigue={fatigue}"
	)


def _extract_generated_text(response: dict) -> str:
	results = response.get("results")
	if isinstance(results, list) and results:
		first = results[0]
		if isinstance(first, dict):
			text = first.get("generated_text")
			if isinstance(text, str):
				return text

	if isinstance(response.get("generated_text"), str):
		return response["generated_text"]

	return str(response)


def _default_race_engineer_system_prompt() -> str:
	return (
		"You are the RaceSight Race Engineer. "
		"Be calm, precise, and actionable. "
		"Use telemetry and coaching/pit/safety inputs to create a concise pit-wall brief. "
		"Never invent data. "
		"Prioritize driver coaching, pit strategy, and safety in that order."
	)


def racesight_granite_call(
	prompt: str,
	system_prompt: str | None = None,
	model_id: str | None = None,
	project_id: str | None = None,
) -> str:
	"""Direct Granite text generation wrapper used by API clients/routes."""
	if not prompt.strip():
		raise ValueError("prompt must not be empty")

	resolved_model = model_id or os.getenv("GRANITE_MODEL")
	if not resolved_model:
		raise ValueError("GRANITE_MODEL is required for direct Granite calls")

	resolved_project = project_id or os.getenv("GRANITE_PROJECT_ID")
	if not resolved_project:
		raise ValueError("GRANITE_PROJECT_ID is required for direct Granite calls")

	input_text = prompt
	if system_prompt and system_prompt.strip():
		input_text = f"System: {system_prompt.strip()}\n\nUser: {prompt}"

	payload = {
		"model_id": resolved_model,
		"project_id": resolved_project,
		"input": input_text,
		"parameters": {
			"decoding_method": "greedy",
			"max_new_tokens": 400,
			"min_new_tokens": 1,
		},
	}

	response = send_to_granite(payload)
	return _extract_generated_text(response)


def racesight_race_engineer_brief(
	race_state: dict[str, Any],
	endpoint: str | None = None,
	api_key: str | None = None,
	model_id: str | None = None,
	project_id: str | None = None,
	focus: str = "balanced",
) -> dict[str, Any]:
	"""Generate a compact pit-wall briefing using the coaching + pit strategy views."""
	coaching = compute_driver_coaching_adapter(
		race_state=race_state,
		endpoint=endpoint,
		api_key=api_key,
		model=model_id,
	)
	pit = compute_pit_strategy_adapter(
		race_state=race_state,
		endpoint=endpoint,
		api_key=api_key,
		model=model_id,
	)
	safety = evaluate_safety_status_adapter(
		race_state=race_state,
		endpoint=endpoint,
		api_key=api_key,
		model=model_id,
	)

	brief_prompt = json.dumps(
		{
			"focus": focus,
			"race_summary": _summarize_race_state(race_state),
			"coaching": coaching,
			"pit_strategy": pit,
			"safety": safety,
			"race_state": race_state,
		},
		indent=2,
	)
	brief_text = racesight_granite_call(
		prompt=(
			"Create a race-engineer brief from this structured telemetry and strategy package. "
			"Return a short title, three bullet actions, and a one-sentence explanation.\n\n"
			+ brief_prompt
		),
		system_prompt=_default_race_engineer_system_prompt(),
		model_id=model_id,
		project_id=project_id,
	)

	return {
		"focus": focus,
		"summary": _summarize_race_state(race_state),
		"coaching": coaching,
		"pit_strategy": pit,
		"safety": safety,
		"brief": brief_text,
	}


def run_driver_coaching_loop(
	series: Iterable[dict[str, Any]] | None = None,
	max_steps: int = 6,
	endpoint: str | None = None,
	api_key: str | None = None,
	model_id: str | None = None,
) -> list[dict[str, Any]]:
	"""Generate a step-by-step coaching loop over a telemetry series."""
	if series is None:
		series = load_telemetry_series()

	steps: list[dict[str, Any]] = []
	for index, snapshot in enumerate(series):
		if index >= max_steps:
			break
		race_state = build_race_state_from_sensor_snapshot(snapshot)
		step = {
			"step": index + 1,
			"summary": _summarize_race_state(race_state),
			"coaching": compute_driver_coaching_adapter(
				race_state=race_state,
				endpoint=endpoint,
				api_key=api_key,
				model=model_id,
			),
			"pit_strategy": compute_pit_strategy_adapter(
				race_state=race_state,
				endpoint=endpoint,
				api_key=api_key,
				model=model_id,
			),
			"safety": evaluate_safety_status_adapter(
				race_state=race_state,
				endpoint=endpoint,
				api_key=api_key,
				model=model_id,
			),
		}
		steps.append(step)
	return steps


def run_race_replay_mode(
	series: Iterable[dict[str, Any]] | None = None,
	max_frames: int = 8,
	include_brief: bool = False,
	endpoint: str | None = None,
	api_key: str | None = None,
	model_id: str | None = None,
	project_id: str | None = None,
) -> list[dict[str, Any]]:
	"""Build a replay timeline from telemetry snapshots."""
	if series is None:
		series = load_telemetry_series()

	frames: list[dict[str, Any]] = []
	for index, snapshot in enumerate(series):
		if index >= max_frames:
			break
		race_state = build_race_state_from_sensor_snapshot(snapshot)
		frame: dict[str, Any] = {
			"frame": index + 1,
			"summary": _summarize_race_state(race_state),
			"state": race_state,
		}
		if include_brief and index in {0, max(0, max_frames - 1)}:
			frame["brief"] = racesight_race_engineer_brief(
				race_state,
				endpoint=endpoint,
				api_key=api_key,
				model_id=model_id,
				project_id=project_id,
			)
		frames.append(frame)
	return frames


def stream_text_chunks(text: str, chunk_size: int = 32) -> Iterable[str]:
	"""Yield text in small chunks for streaming responses."""
	for index in range(0, len(text), chunk_size):
		yield text[index : index + chunk_size]
