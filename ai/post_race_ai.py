from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .granite_orchestrator_loader import extract_message_from_granite_response, send_to_granite


PROMPT_FILE = Path(__file__).resolve().parent / "prompts" / "post_race_prompt.txt"
DEFAULT_POST_RACE_PROMPT = (
	"You are RaceSight Post-Race AI. Generate a structured post-race summary from race_log. "
	"Return JSON with keys: summary_text, key_moments, strategy_evaluation, driver_performance, "
	"safety_interventions, recommendations."
)


def _load_post_race_prompt() -> str:
	if PROMPT_FILE.exists():
		text = PROMPT_FILE.read_text(encoding="utf-8").strip()
		if text:
			return text
	return DEFAULT_POST_RACE_PROMPT


def generate_post_race_summary_adapter(
	race_log: list[dict[str, Any]],
	endpoint: str | None = None,
	api_key: str | None = None,
	model: str | None = None,
) -> dict[str, Any]:
	prompt = _load_post_race_prompt()
	payload: dict[str, Any] = {
		"messages": [
			{"role": "system", "content": prompt},
			{
				"role": "user",
				"content": (
					"Generate post-race summary from this race_log JSON. Return JSON only.\n"
					+ json.dumps(race_log)
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
			"summary_text": content,
			"key_moments": [],
			"strategy_evaluation": {},
			"driver_performance": {},
			"safety_interventions": [],
			"recommendations": [],
		}
	return {
		"summary_text": "No post-race summary content returned",
		"key_moments": [],
		"strategy_evaluation": {},
		"driver_performance": {},
		"safety_interventions": [],
		"recommendations": [],
	}