from __future__ import annotations

from fastapi.testclient import TestClient

from ai.orchestrator import granite_client


def test_chat_endpoint_returns_orchestrator_response(monkeypatch) -> None:
    monkeypatch.setattr(
        granite_client,
        "racesight_orchestrator",
        lambda message: f"handled:{message}",
    )
    client = TestClient(granite_client.app)

    response = client.post("/chat", json={"message": "What now?"})

    assert response.status_code == 200
    assert response.json() == {"response": "handled:What now?"}


def test_chat_endpoint_validates_payload() -> None:
    client = TestClient(granite_client.app)

    response = client.post("/chat", json={})

    assert response.status_code == 422


def test_granite_endpoint_returns_wrapper_response(monkeypatch) -> None:
    monkeypatch.setattr(
        granite_client,
        "racesight_granite_call",
        lambda prompt, system_prompt=None: f"granite:{prompt}:{system_prompt}",
    )
    client = TestClient(granite_client.app)

    response = client.post(
        "/granite",
        json={"prompt": "race update", "system_prompt": "be concise"},
    )

    assert response.status_code == 200
    assert response.json() == {"response": "granite:race update:be concise"}
