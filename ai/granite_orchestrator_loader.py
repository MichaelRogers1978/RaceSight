from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from urllib import error, request


DEFAULT_EMBEDDED_CONFIG_FILE = "granite_orchestrator_agent_config.embedded.json"
DEFAULT_GRANITE_TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class EmbeddedGraniteAgentConfig:
    name: str
    description: str
    system_prompt: str
    tool_choice: Literal["auto"]
    tools: list[dict[str, Any]]


def _require_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _validate_tool(tool: Any, index: int) -> dict[str, Any]:
    if not isinstance(tool, dict):
        raise TypeError(f"tools[{index}] must be an object")

    required_keys = {"name", "description", "parameters"}
    missing = required_keys.difference(tool.keys())
    if missing:
        raise ValueError(f"tools[{index}] is missing required keys: {sorted(missing)}")

    for field_name in ("name", "description"):
        _require_non_empty_string(tool.get(field_name), f"tools[{index}].{field_name}")

    parameters = tool.get("parameters")
    if not isinstance(parameters, dict):
        raise TypeError(f"tools[{index}].parameters must be an object")

    return tool


def _validate_embedded_config(raw_config: Any) -> EmbeddedGraniteAgentConfig:
    if not isinstance(raw_config, dict):
        raise TypeError("Embedded Granite config must be a JSON object")

    name = _require_non_empty_string(raw_config.get("name"), "name")
    description = _require_non_empty_string(raw_config.get("description"), "description")
    system_prompt = _require_non_empty_string(raw_config.get("system_prompt"), "system_prompt")

    tool_choice = raw_config.get("tool_choice")
    if tool_choice != "auto":
        raise ValueError("tool_choice must be 'auto'")

    tools = raw_config.get("tools")
    if not isinstance(tools, list) or not tools:
        raise ValueError("tools must be a non-empty array")

    validated_tools = [_validate_tool(tool, index) for index, tool in enumerate(tools)]

    return EmbeddedGraniteAgentConfig(
        name=name,
        description=description,
        system_prompt=system_prompt,
        tool_choice="auto",
        tools=validated_tools,
    )


def load_embedded_orchestrator_config(
    config_path: str | Path | None = None,
) -> EmbeddedGraniteAgentConfig:
    """Load and validate the self-contained Granite orchestrator config."""
    base_dir = Path(__file__).resolve().parent
    target = Path(config_path) if config_path else base_dir / DEFAULT_EMBEDDED_CONFIG_FILE

    with target.open("r", encoding="utf-8") as file_handle:
        raw_config = json.load(file_handle)

    return _validate_embedded_config(raw_config)


def build_granite_request_payload(
    user_message: str,
    config_path: str | Path | None = None,
    model: str | None = None,
    prior_messages: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Build a Granite request payload from the embedded orchestrator config.

    The returned payload is ready to send to a Granite chat/function-calling API
    that accepts system and user messages plus a tools array.
    """
    if not user_message.strip():
        raise ValueError("user_message must not be empty")

    config = load_embedded_orchestrator_config(config_path)
    messages = [{"role": "system", "content": config.system_prompt}]

    if prior_messages:
        messages.extend(prior_messages)

    messages.append({"role": "user", "content": user_message})

    payload: dict[str, Any] = {
        "messages": messages,
        "tools": config.tools,
        "tool_choice": config.tool_choice,
    }

    if model:
        payload["model"] = model

    return payload


def send_to_granite(
    payload: dict[str, Any],
    endpoint: str | None = None,
    api_key: str | None = None,
    timeout_seconds: int = DEFAULT_GRANITE_TIMEOUT_SECONDS,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """POST a Granite request payload to the configured Granite endpoint."""
    target_endpoint = endpoint or os.getenv("GRANITE_ENDPOINT")
    if not target_endpoint:
        raise ValueError("Granite endpoint is required. Set GRANITE_ENDPOINT or pass endpoint.")

    auth_key = api_key or os.getenv("GRANITE_API_KEY")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if auth_key:
        headers["Authorization"] = f"Bearer {auth_key}"
    if extra_headers:
        headers.update(extra_headers)

    request_body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        url=target_endpoint,
        data=request_body,
        headers=headers,
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=timeout_seconds) as response:
            response_text = response.read().decode("utf-8")
    except error.HTTPError as exc:
        response_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Granite request failed with HTTP {exc.code}: {response_text}"
        ) from exc
    except error.URLError as exc:
        raise RuntimeError(f"Granite request failed: {exc.reason}") from exc

    try:
        return json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise ValueError("Granite response was not valid JSON") from exc


def extract_message_from_granite_response(response: dict[str, Any]) -> dict[str, Any]:
    """Extract the first assistant message from common Granite/OpenAI-style responses."""
    if "choices" in response and isinstance(response["choices"], list) and response["choices"]:
        first_choice = response["choices"][0]
        if isinstance(first_choice, dict):
            message = first_choice.get("message")
            if isinstance(message, dict):
                return message

    if "output" in response and isinstance(response["output"], dict):
        message = response["output"].get("message")
        if isinstance(message, dict):
            return message

    raise ValueError("Unable to locate assistant message in Granite response")


def example_request_payload() -> dict[str, Any]:
    """Return a sample Granite request payload for local inspection/testing."""
    return build_granite_request_payload(
        user_message="What should we do now?",
        prior_messages=[
            {
                "role": "assistant",
                "content": "Awaiting latest race context or tool decision.",
            }
        ],
    )


if __name__ == "__main__":
    request_payload = example_request_payload()
    print(json.dumps(request_payload, indent=2))