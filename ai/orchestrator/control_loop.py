from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from types import ModuleType

from ai.granite_orchestrator_loader import send_to_granite


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
