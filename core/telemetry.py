from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib import request


DEFAULT_SENSOR_FEED_FILE = "data/live_sensor_feed.json"
DEFAULT_SENSOR_FEED_TIMEOUT_SECONDS = 5


class TelemetryFeedError(RuntimeError):
	"""Raised when a telemetry feed cannot be loaded or parsed."""


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
