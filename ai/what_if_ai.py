from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .granite_orchestrator_loader import extract_message_from_granite_response, send_to_granite


PROMPT_FILE = Path(__file__).resolve().parent / "prompts" / "outcome_prompt.txt"
DEFAULT_WHAT_IF_PROMPT = (
	"You are RaceSight What-If AI. Simulate alternative race outcomes from race_state and scenario. "
	"Return JSON with keys: scenario, projected_outcome, tradeoffs, recommendation."
)


def _load_what_if_prompt() -> str:
	if PROMPT_FILE.exists():
		text = PROMPT_FILE.read_text(encoding="utf-8").strip()
		if text:
			return text
	return DEFAULT_WHAT_IF_PROMPT


def run_what_if_scenario_adapter(
	race_state: dict[str, Any],
	scenario: str,
	endpoint: str | None = None,
	api_key: str | None = None,
	model: str | None = None,
) -> dict[str, Any]:
	prompt = _load_what_if_prompt()
	payload: dict[str, Any] = {
		"messages": [
			{"role": "system", "content": prompt},
			{
				"role": "user",
				"content": (
					"Run a what-if simulation using this RaceState JSON and scenario. "
					"Return JSON only.\n"
					+ json.dumps({"scenario": scenario, "race_state": race_state})
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
			"scenario": scenario,
			"projected_outcome": content,
			"tradeoffs": [],
			"recommendation": "No structured recommendation returned",
		}
	return {
		"scenario": scenario,
		"projected_outcome": "No simulation content returned",
		"tradeoffs": [],
		"recommendation": "No structured recommendation returned",
	}
