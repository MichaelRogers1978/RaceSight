from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AI_DIR = ROOT / "ai"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai.granite_orchestrator_loader import load_embedded_orchestrator_config
from ai.pydantic_models import RuntimeToolRegistration


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file_handle:
        payload = json.load(file_handle)
    if not isinstance(payload, dict):
        raise TypeError(f"Expected object at {path}")
    return payload


def validate_runtime_registration() -> None:
    strict_path = AI_DIR / "granite_tool_registration.runtime.strict.json"
    payload = _load_json(strict_path)
    RuntimeToolRegistration.model_validate(payload)


def validate_embedded_config() -> None:
    load_embedded_orchestrator_config(AI_DIR / "granite_orchestrator_agent_config.embedded.json")


def validate_json_files_parse() -> None:
    for path in sorted(AI_DIR.glob("*.json")):
        _load_json(path)


def main() -> int:
    validate_json_files_parse()
    validate_runtime_registration()
    validate_embedded_config()
    print("Schema validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
