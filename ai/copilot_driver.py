from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .granite_orchestrator_loader import extract_message_from_granite_response, send_to_granite


PROMPT_FILE = Path(__file__).resolve().parent / "prompts" / "driver_prompt.txt"
DEFAULT_DRIVER_PROMPT = (
	"You are RaceSight Driver Copilot. Provide concise, turn-by-turn coaching guidance "
	"based only on the provided race_state. Return JSON with keys: coaching_summary, "
	"actions (array), and risk_notes (array)."
)


def _load_driver_prompt() -> str:
	if PROMPT_FILE.exists():
		text = PROMPT_FILE.read_text(encoding="utf-8").strip()
		if text:
			return text
	return DEFAULT_DRIVER_PROMPT


def compute_driver_coaching_adapter(
	race_state: dict[str, Any],
	endpoint: str | None = None,
	api_key: str | None = None,
	model: str | None = None,
) -> dict[str, Any]:
	prompt = _load_driver_prompt()
	payload: dict[str, Any] = {
		"messages": [
			{"role": "system", "content": prompt},
			{
				"role": "user",
				"content": (
					"Generate driver coaching from this RaceState JSON. "
					"Return JSON only.\n" + json.dumps(race_state)
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
		return {"coaching_summary": content, "actions": [], "risk_notes": []}
	return {"coaching_summary": "No coaching content returned", "actions": [], "risk_notes": []}
