from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.granite_orchestrator_loader import (  # noqa: E402
    build_granite_request_payload,
    extract_message_from_granite_response,
    load_embedded_orchestrator_config,
    send_to_granite,
)
from ai.copilot_driver import compute_driver_coaching_adapter  # noqa: E402
from ai.pit_boss import compute_pit_strategy_adapter  # noqa: E402
from ai.safety_ai import evaluate_safety_status_adapter  # noqa: E402
from ai.what_if_ai import run_what_if_scenario_adapter  # noqa: E402
from ai.schema_usage import (  # noqa: E402
    ToolExecutor,
    example_race_state_payload,
    invoke_tool_with_validation,
)


_EMBEDDED_CONFIG = load_embedded_orchestrator_config()
RACESIGHT_ORCHESTRATOR_PROMPT = _EMBEDDED_CONFIG.system_prompt
RACESIGHT_TOOL_SCHEMAS = _EMBEDDED_CONFIG.tools

SYSTEM_PROMPT = RACESIGHT_ORCHESTRATOR_PROMPT
TOOLS = RACESIGHT_TOOL_SCHEMAS


def _parse_tool_arguments(arguments: Any) -> dict[str, Any]:
    if isinstance(arguments, dict):
        return arguments
    if isinstance(arguments, str):
        parsed = json.loads(arguments) if arguments.strip() else {}
        if not isinstance(parsed, dict):
            raise TypeError("Tool call arguments must decode to an object")
        return parsed
    if arguments is None:
        return {}
    raise TypeError("Tool call arguments must be a JSON string or object")


def _extract_single_tool_call(message: dict[str, Any]) -> dict[str, Any] | None:
    tool_calls = message.get("tool_calls")
    if isinstance(tool_calls, list) and tool_calls:
        if len(tool_calls) != 1:
            raise ValueError("RaceSight Orchestrator expects exactly one tool call per turn")
        tool_call = tool_calls[0]
        if not isinstance(tool_call, dict):
            raise TypeError("tool_calls[0] must be an object")
        if "function" in tool_call and isinstance(tool_call["function"], dict):
            function_block = tool_call["function"]
            return {
                "id": tool_call.get("id", "tool-call-1"),
                "name": function_block.get("name"),
                "arguments": function_block.get("arguments", {}),
            }
        return {
            "id": tool_call.get("id", "tool-call-1"),
            "name": tool_call.get("name"),
            "arguments": tool_call.get("arguments", {}),
        }

    function_call = message.get("function_call")
    if isinstance(function_call, dict):
        return {
            "id": function_call.get("id", "function-call-1"),
            "name": function_call.get("name"),
            "arguments": function_call.get("arguments", {}),
        }

    return None


def _message_content_as_text(message: dict[str, Any]) -> str:
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_value = item.get("text")
                if isinstance(text_value, str):
                    parts.append(text_value)
        return "\n".join(parts)
    return ""


def _extract_tool_calls_from_message(message: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize assistant tool call shape into [{'id','name','arguments'}]."""
    normalized: list[dict[str, Any]] = []
    raw_calls = message.get("tool_calls")
    if isinstance(raw_calls, list):
        for index, tool_call in enumerate(raw_calls, start=1):
            if not isinstance(tool_call, dict):
                continue
            if "function" in tool_call and isinstance(tool_call["function"], dict):
                function_block = tool_call["function"]
                normalized.append(
                    {
                        "id": tool_call.get("id", f"tool-call-{index}"),
                        "name": function_block.get("name"),
                        "arguments": function_block.get("arguments", {}),
                    }
                )
                continue
            normalized.append(
                {
                    "id": tool_call.get("id", f"tool-call-{index}"),
                    "name": tool_call.get("name"),
                    "arguments": tool_call.get("arguments", {}),
                }
            )
    return normalized


def _normalize_response_for_loop(response: dict[str, Any]) -> dict[str, Any]:
    """Convert Granite response into loop-friendly shape with content/tool_calls keys."""
    message = extract_message_from_granite_response(response)
    normalized: dict[str, Any] = {
        "content": _message_content_as_text(message),
    }
    tool_calls = _extract_tool_calls_from_message(message)
    if tool_calls:
        normalized["tool_calls"] = tool_calls
    return normalized


def call_llm_with_tools(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    endpoint: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Send one turn to Granite and return normalized content/tool_calls response."""
    payload: dict[str, Any] = {
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
    }
    if model:
        payload["model"] = model
    raw_response = send_to_granite(payload, endpoint=endpoint, api_key=api_key)
    return _normalize_response_for_loop(raw_response)


# --- Backend implementations ---
def get_race_state() -> Dict[str, Any]:
    return example_race_state_payload()


def compute_driver_coaching(race_state: Dict[str, Any]) -> Dict[str, Any]:
    return compute_driver_coaching_adapter(
        race_state=race_state,
        endpoint=RUNTIME_GRANITE_ENDPOINT,
        api_key=RUNTIME_GRANITE_API_KEY,
        model=RUNTIME_GRANITE_MODEL,
    )


def compute_pit_strategy(race_state: Dict[str, Any]) -> Dict[str, Any]:
    return compute_pit_strategy_adapter(
        race_state=race_state,
        endpoint=RUNTIME_GRANITE_ENDPOINT,
        api_key=RUNTIME_GRANITE_API_KEY,
        model=RUNTIME_GRANITE_MODEL,
    )


def evaluate_safety_status(race_state: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate_safety_status_adapter(
        race_state=race_state,
        endpoint=RUNTIME_GRANITE_ENDPOINT,
        api_key=RUNTIME_GRANITE_API_KEY,
        model=RUNTIME_GRANITE_MODEL,
    )


def run_what_if_scenario(race_state: Dict[str, Any], scenario: str) -> Dict[str, Any]:
    return run_what_if_scenario_adapter(
        race_state=race_state,
        scenario=scenario,
        endpoint=RUNTIME_GRANITE_ENDPOINT,
        api_key=RUNTIME_GRANITE_API_KEY,
        model=RUNTIME_GRANITE_MODEL,
    )


def generate_post_race_summary(race_log: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "status": "stub",
        "tool": "generate_post_race_summary",
        "message": "Replace with real post-race summary implementation.",
        "events_count": len(race_log),
    }


TOOL_DISPATCH = {
    "get_race_state": get_race_state,
    "compute_driver_coaching": compute_driver_coaching,
    "compute_pit_strategy": compute_pit_strategy,
    "evaluate_safety_status": evaluate_safety_status,
    "run_what_if_scenario": run_what_if_scenario,
    "generate_post_race_summary": generate_post_race_summary,
}

RUNTIME_GRANITE_ENDPOINT: str | None = None
RUNTIME_GRANITE_API_KEY: str | None = None
RUNTIME_GRANITE_MODEL: str | None = None


def _build_executors_from_tool_dispatch() -> dict[str, ToolExecutor]:
    """Adapt TOOL_DISPATCH signatures to payload-style executors for validated invocation."""
    return {
        "get_race_state": lambda _payload: TOOL_DISPATCH["get_race_state"](),
        "compute_driver_coaching": lambda payload: TOOL_DISPATCH["compute_driver_coaching"](
            payload["race_state"]
        ),
        "compute_pit_strategy": lambda payload: TOOL_DISPATCH["compute_pit_strategy"](
            payload["race_state"]
        ),
        "evaluate_safety_status": lambda payload: TOOL_DISPATCH["evaluate_safety_status"](
            payload["race_state"]
        ),
        "run_what_if_scenario": lambda payload: TOOL_DISPATCH["run_what_if_scenario"](
            payload["race_state"], payload["scenario"]
        ),
        "generate_post_race_summary": lambda payload: TOOL_DISPATCH[
            "generate_post_race_summary"
        ](payload["race_log"]),
    }


# --- Single-turn orchestration with tool calling ---
def racesight_orchestrator(
    user_message: str,
    endpoint: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
) -> str:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    executors = _build_executors_from_tool_dispatch()

    for _ in range(4):
        response = call_llm_with_tools(
            messages=messages,
            tools=TOOLS,
            endpoint=endpoint,
            api_key=api_key,
            model=model,
        )

        if "tool_calls" in response:
            for tool_call in response["tool_calls"]:
                tool_name = tool_call["name"]
                tool_args = _parse_tool_arguments(tool_call.get("arguments", {}))

                if tool_name in {
                    "compute_driver_coaching",
                    "compute_pit_strategy",
                    "evaluate_safety_status",
                    "run_what_if_scenario",
                } and "race_state" not in tool_args:
                    tool_args["race_state"] = get_race_state()

                result = invoke_tool_with_validation(tool_name, tool_args, executors)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.get("id", "tool-call-1"),
                        "name": tool_name,
                        "content": json.dumps(result),
                    }
                )

            continue

        if "content" in response and isinstance(response["content"], str):
            return response["content"]

    return "I was unable to produce a final answer after several tool calls."


def build_default_demo_executors() -> dict[str, ToolExecutor]:
    """Demo-only executors for local end-to-end plumbing checks."""

    def get_race_state(_: dict[str, Any]) -> dict[str, Any]:
        return example_race_state_payload()

    def not_implemented(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "demo-only",
            "message": "Replace this demo executor with your real RaceSight implementation.",
            "validated_payload_keys": sorted(payload.keys()),
        }

    return {
        "get_race_state": get_race_state,
        "compute_driver_coaching": not_implemented,
        "compute_pit_strategy": not_implemented,
        "evaluate_safety_status": not_implemented,
        "run_what_if_scenario": not_implemented,
        "generate_post_race_summary": not_implemented,
    }


def dispatch_tool_call(
    tool_call: dict[str, Any],
    executors: dict[str, ToolExecutor],
) -> tuple[str, dict[str, Any], Any]:
    tool_name = tool_call.get("name")
    if not isinstance(tool_name, str) or not tool_name.strip():
        raise ValueError("Granite tool call is missing a valid function name")

    payload = _parse_tool_arguments(tool_call.get("arguments"))
    result = invoke_tool_with_validation(tool_name, payload, executors)
    return tool_name, payload, result


def build_follow_up_payload(
    user_message: str,
    assistant_message: dict[str, Any],
    tool_call_id: str,
    tool_name: str,
    tool_result: Any,
    config_path: str | Path | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    config = load_embedded_orchestrator_config(config_path)
    messages = [
        {"role": "system", "content": config.system_prompt},
        {"role": "user", "content": user_message},
        assistant_message,
        {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": json.dumps(tool_result),
        },
    ]

    payload: dict[str, Any] = {
        "messages": messages,
        "tools": config.tools,
        "tool_choice": config.tool_choice,
    }
    if model:
        payload["model"] = model
    return payload


def run_orchestrator_turn(
    user_message: str,
    executors: dict[str, ToolExecutor],
    endpoint: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    initial_payload = build_granite_request_payload(
        user_message=user_message,
        config_path=config_path,
        model=model,
    )
    initial_response = send_to_granite(initial_payload, endpoint=endpoint, api_key=api_key)
    assistant_message = extract_message_from_granite_response(initial_response)
    tool_call = _extract_single_tool_call(assistant_message)

    if tool_call is None:
        return {
            "mode": "direct_response",
            "assistant_text": _message_content_as_text(assistant_message),
            "initial_response": initial_response,
        }

    tool_name, tool_payload, tool_result = dispatch_tool_call(tool_call, executors)
    follow_up_payload = build_follow_up_payload(
        user_message=user_message,
        assistant_message=assistant_message,
        tool_call_id=str(tool_call.get("id", "tool-call-1")),
        tool_name=tool_name,
        tool_result=tool_result,
        config_path=config_path,
        model=model,
    )
    final_response = send_to_granite(follow_up_payload, endpoint=endpoint, api_key=api_key)
    final_message = extract_message_from_granite_response(final_response)

    return {
        "mode": "tool_response",
        "tool_name": tool_name,
        "tool_payload": tool_payload,
        "tool_result": tool_result,
        "assistant_text": _message_content_as_text(final_message),
        "initial_response": initial_response,
        "final_response": final_response,
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RaceSight Granite orchestrator entrypoint")
    parser.add_argument("message", help="User message to send to the orchestrator")
    parser.add_argument("--endpoint", help="Granite HTTP endpoint. Defaults to GRANITE_ENDPOINT")
    parser.add_argument("--api-key", help="Granite API key. Defaults to GRANITE_API_KEY")
    parser.add_argument("--model", help="Optional Granite model identifier")
    parser.add_argument("--config", help="Optional embedded config JSON path")
    parser.add_argument(
        "--print-payload-only",
        action="store_true",
        help="Print the first-turn Granite payload without sending it",
    )
    parser.add_argument(
        "--demo-executors",
        action="store_true",
        help="Use demo tool executors for plumbing tests",
    )
    parser.add_argument(
        "--legacy-turn",
        action="store_true",
        help="Use legacy one-tool-turn flow instead of the iterative control loop",
    )
    return parser


def main() -> int:
    global RUNTIME_GRANITE_ENDPOINT, RUNTIME_GRANITE_API_KEY, RUNTIME_GRANITE_MODEL

    parser = build_argument_parser()
    args = parser.parse_args()

    RUNTIME_GRANITE_ENDPOINT = args.endpoint
    RUNTIME_GRANITE_API_KEY = args.api_key
    RUNTIME_GRANITE_MODEL = args.model

    if args.print_payload_only:
        payload = build_granite_request_payload(
            user_message=args.message,
            config_path=args.config,
            model=args.model,
        )
        print(json.dumps(payload, indent=2))
        return 0

    if args.legacy_turn:
        executors = build_default_demo_executors() if args.demo_executors else _build_executors_from_tool_dispatch()
        result = run_orchestrator_turn(
            user_message=args.message,
            executors=executors,
            endpoint=args.endpoint,
            api_key=args.api_key,
            model=args.model,
            config_path=args.config,
        )
        print(json.dumps(result, indent=2))
        return 0

    assistant_text = racesight_orchestrator(
        user_message=args.message,
        endpoint=args.endpoint,
        api_key=args.api_key,
        model=args.model,
    )
    print(assistant_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
