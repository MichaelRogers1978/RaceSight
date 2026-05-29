from __future__ import annotations

import os
from typing import Any

import requests


def call_granite(prompt: str, system_prompt: str | None = None) -> str:
    endpoint = os.getenv("GRANITE_ENDPOINT")
    api_key = os.getenv("GRANITE_API_KEY")
    model_id = os.getenv("GRANITE_MODEL")
    project_id = os.getenv("GRANITE_PROJECT_ID")

    if not endpoint or not api_key or not model_id or not project_id:
        raise ValueError(
            "Missing env vars. Required: GRANITE_ENDPOINT, GRANITE_API_KEY, GRANITE_MODEL, GRANITE_PROJECT_ID"
        )

    input_text = prompt.strip()
    if system_prompt and system_prompt.strip():
        input_text = f"System: {system_prompt.strip()}\\n\\nUser: {input_text}"

    payload: dict[str, Any] = {
        "model_id": model_id,
        "project_id": project_id,
        "input": input_text,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 400,
            "min_new_tokens": 1,
        },
    }

    response = requests.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json=payload,
        timeout=60,
    )
    response.raise_for_status()

    data = response.json()
    results = data.get("results")
    if isinstance(results, list) and results:
        first = results[0]
        if isinstance(first, dict) and isinstance(first.get("generated_text"), str):
            return first["generated_text"]

    if isinstance(data.get("generated_text"), str):
        return data["generated_text"]

    return str(data)


if __name__ == "__main__":
    text = call_granite("What should we do now?", system_prompt="You are RaceSight race engineer.")
    print(text)
