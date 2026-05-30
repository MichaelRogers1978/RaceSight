from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib import request


DEFAULT_SENSOR_FEED_FILE = "data/live_sensor_feed.json"
DEFAULT_REPLAY_FEED_FILE = "data/race_replay_sample.json"
DEFAULT_SENSOR_FEED_TIMEOUT_SECONDS = 5


class TelemetryFeedError(RuntimeError):
	"""Raised when a telemetry feed cannot be loaded or parsed."""


class TelemetrySeriesError(RuntimeError):
	"""Raised when a telemetry replay series cannot be loaded or parsed."""


def _load_from_file(path: str | Path) -> dict[str, Any]:
	file_path = Path(path)
	if not file_path.exists():
		raise TelemetryFeedError(f"Telemetry file not found: {file_path}")

	try:
		return json.loads(file_path.read_text(encoding="utf-8"))
	except json.JSONDecodeError as exc:
		raise TelemetryFeedError(f"Telemetry file is not valid JSON: {file_path}") from exc


def _load_from_url(url: str, timeout_seconds: int) -> dict[str, Any]:
	http_request = request.Request(
		url=url,
		headers={"Accept": "application/json"},
		method="GET",
	)
	try:
		with request.urlopen(http_request, timeout=timeout_seconds) as response:
			raw = response.read().decode("utf-8")
	except Exception as exc:
		raise TelemetryFeedError(f"Telemetry HTTP source failed: {exc}") from exc

	try:
		return json.loads(raw)
	except json.JSONDecodeError as exc:
		raise TelemetryFeedError("Telemetry HTTP source returned non-JSON content") from exc


def _load_series_from_url(url: str, timeout_seconds: int) -> list[dict[str, Any]]:
	http_request = request.Request(
		url=url,
		headers={"Accept": "application/json"},
		method="GET",
	)
	try:
		with request.urlopen(http_request, timeout=timeout_seconds) as response:
			raw = response.read().decode("utf-8")
	except Exception as exc:
		raise TelemetrySeriesError(f"Telemetry replay HTTP source failed: {exc}") from exc

	try:
		payload = json.loads(raw)
	except json.JSONDecodeError as exc:
		raise TelemetrySeriesError("Telemetry replay HTTP source returned non-JSON content") from exc

	return _coerce_replay_series(payload)


def _coerce_replay_series(payload: Any) -> list[dict[str, Any]]:
	if isinstance(payload, list):
		series = payload
	elif isinstance(payload, dict) and isinstance(payload.get("frames"), list):
		series = payload["frames"]
	elif isinstance(payload, dict):
		series = [payload]
	else:
		raise TelemetrySeriesError("Telemetry replay payload must be a JSON object or array")

	frames: list[dict[str, Any]] = []
	for index, frame in enumerate(series):
		if not isinstance(frame, dict):
			raise TelemetrySeriesError(f"Replay frame {index} must be a JSON object")
		if "car" not in frame or "race" not in frame:
			raise TelemetrySeriesError(f"Replay frame {index} missing required keys: car, race")
		frames.append(frame)

	if not frames:
		raise TelemetrySeriesError("Telemetry replay series cannot be empty")
	return frames


def load_sensor_snapshot(
	source_file: str | Path | None = None,
	source_url: str | None = None,
	timeout_seconds: int = DEFAULT_SENSOR_FEED_TIMEOUT_SECONDS,
) -> dict[str, Any]:
	"""Load a single live telemetry snapshot from configured sensor feed source.

	Supported sources:
	- File path via argument, or env RACESIGHT_SENSOR_FEED_FILE
	- HTTP URL via argument, or env RACESIGHT_SENSOR_FEED_URL
	"""
	resolved_url = source_url or os.getenv("RACESIGHT_SENSOR_FEED_URL")
	if resolved_url:
		payload = _load_from_url(resolved_url, timeout_seconds)
	else:
		resolved_file = source_file or os.getenv("RACESIGHT_SENSOR_FEED_FILE") or DEFAULT_SENSOR_FEED_FILE
		payload = _load_from_file(resolved_file)

	if not isinstance(payload, dict):
		raise TelemetryFeedError("Telemetry payload must be a JSON object")
	if "car" not in payload or "race" not in payload:
		raise TelemetryFeedError("Telemetry payload missing required top-level keys: car, race")
	return payload


def load_telemetry_series(
	series_file: str | Path | None = None,
	series_url: str | None = None,
	timeout_seconds: int = DEFAULT_SENSOR_FEED_TIMEOUT_SECONDS,
) -> list[dict[str, Any]]:
	"""Load a telemetry replay series from a JSON array, a frames object, or a single frame."""
	resolved_url = series_url or os.getenv("RACESIGHT_REPLAY_FEED_URL")
	if resolved_url:
		return _load_series_from_url(resolved_url, timeout_seconds)

	resolved_file = series_file or os.getenv("RACESIGHT_REPLAY_FEED_FILE") or DEFAULT_REPLAY_FEED_FILE
	path = Path(resolved_file)
	if not path.exists():
		raise TelemetrySeriesError(f"Telemetry replay file not found: {path}")

	try:
		payload = json.loads(path.read_text(encoding="utf-8"))
	except json.JSONDecodeError as exc:
		raise TelemetrySeriesError(f"Telemetry replay file is not valid JSON: {path}") from exc

	return _coerce_replay_series(payload)
