from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .granite_orchestrator_loader import extract_message_from_granite_response, send_to_granite


PROMPT_FILE = Path(__file__).resolve().parent / "prompts" / "pit_prompt.txt"
DEFAULT_PIT_PROMPT = (
	"You are RaceSight Pit Boss strategist. Compute pit strategy from race_state. "
	"Return JSON with keys: should_pit_now, pit_window, actions, rationale, confidence."
)


def _load_pit_prompt() -> str:
	if PROMPT_FILE.exists():
		text = PROMPT_FILE.read_text(encoding="utf-8").strip()
		if text:
			return text
	return DEFAULT_PIT_PROMPT


def compute_pit_strategy_adapter(
	race_state: dict[str, Any],
	endpoint: str | None = None,
	api_key: str | None = None,
	model: str | None = None,
) -> dict[str, Any]:
	prompt = _load_pit_prompt()
	payload: dict[str, Any] = {
		"messages": [
			{"role": "system", "content": prompt},
			{
				"role": "user",
				"content": (
					"Compute pit strategy from this RaceState JSON. Return JSON only.\n"
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
			"should_pit_now": False,
			"pit_window": {},
			"actions": [],
			"rationale": content,
			"confidence": 0,
		}
	return {
		"should_pit_now": False,
		"pit_window": {},
		"actions": [],
		"rationale": "No pit strategy content returned",
		"confidence": 0,
	}
