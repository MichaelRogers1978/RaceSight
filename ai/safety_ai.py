from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .granite_orchestrator_loader import extract_message_from_granite_response, send_to_granite


PROMPT_FILE = Path(__file__).resolve().parent / "prompts" / "safety_prompt.txt"
DEFAULT_SAFETY_PROMPT = (
	"You are RaceSight Safety AI. Evaluate safety risk and compliance from race_state. "
	"Return JSON with keys: safety_alert_active, alert_level, alert_reason, recommended_action."
)


def _load_safety_prompt() -> str:
	if PROMPT_FILE.exists():
		text = PROMPT_FILE.read_text(encoding="utf-8").strip()
		if text:
			return text
	return DEFAULT_SAFETY_PROMPT


def evaluate_safety_status_adapter(
	race_state: dict[str, Any],
	endpoint: str | None = None,
	api_key: str | None = None,
	model: str | None = None,
) -> dict[str, Any]:
	prompt = _load_safety_prompt()
	payload: dict[str, Any] = {
		"messages": [
			{"role": "system", "content": prompt},
			{
				"role": "user",
				"content": (
					"Evaluate safety status from this RaceState JSON. Return JSON only.\n"
					+ json.dumps(race_state)
				),
			},
		]
	}
	if model:
		payload["model"] = model

	response = send_to_granite(payload, endpoint=endpoint, api_key=api_key)
	message = extract_message_from_granite_response(response)
	content = message.get("content", "")
	if isinstance(content, str):
		try:
			parsed = json.loads(content)
			if isinstance(parsed, dict):
				return parsed
		except json.JSONDecodeError:
			pass
		return {
			"safety_alert_active": False,
			"alert_level": "unknown",
			"alert_reason": content,
			"recommended_action": "Review manually",
		}
	return {
		"safety_alert_active": False,
		"alert_level": "unknown",
		"alert_reason": "No safety content returned",
		"recommended_action": "Review manually",
	}
