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


def test_frontend_root_serves_index_html() -> None:
    client = TestClient(granite_client.app)

    response = client.get("/")

    assert response.status_code == 200
    assert "RaceSight Control Room" in response.text


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


def test_racesight_router_endpoint_returns_orchestrator_response(monkeypatch) -> None:
    monkeypatch.setattr(
        "ai.orchestrator.routes.racesight_orchestrator",
        lambda message: f"router:{message}",
    )
    client = TestClient(granite_client.app)

    response = client.post("/racesight", json={"message": "status"})

    assert response.status_code == 200
    assert response.json() == {"response": "router:status"}


def test_racesight_router_granite_endpoint_returns_wrapper_response(monkeypatch) -> None:
    monkeypatch.setattr(
        "ai.orchestrator.routes.racesight_granite_call",
        lambda prompt, system_prompt=None: f"router-granite:{prompt}:{system_prompt}",
    )
    client = TestClient(granite_client.app)

    response = client.post(
        "/racesight/granite",
        json={"prompt": "pit now", "system_prompt": "short"},
    )

    assert response.status_code == 200
    assert response.json() == {"response": "router-granite:pit now:short"}


def test_racesight_router_brief_endpoint_returns_brief(monkeypatch) -> None:
    monkeypatch.setattr(
        "ai.orchestrator.routes.get_race_state",
        lambda: {"race_context": {"race_lap": 12}},
    )
    monkeypatch.setattr(
        "ai.orchestrator.routes.racesight_race_engineer_brief",
        lambda race_state, focus="balanced": {"brief": f"{focus}:{race_state['race_context']['race_lap']}"},
    )
    client = TestClient(granite_client.app)

    response = client.post("/racesight/brief", json={"focus": "aggressive"})

    assert response.status_code == 200
    assert response.json() == {"brief": "aggressive:12"}


def test_racesight_router_replay_endpoint_returns_frames(monkeypatch) -> None:
    monkeypatch.setattr(
        "ai.orchestrator.routes.run_race_replay_mode",
        lambda max_frames=6, include_brief=True: [{"frame": 1, "summary": "ok"}],
    )
    client = TestClient(granite_client.app)

    response = client.post("/racesight/replay", json={"max_frames": 1, "include_brief": True})

    assert response.status_code == 200
    assert response.json() == {"frames": [{"frame": 1, "summary": "ok"}]}


def test_racesight_router_coach_loop_endpoint_returns_steps(monkeypatch) -> None:
    monkeypatch.setattr(
        "ai.orchestrator.routes.run_driver_coaching_loop",
        lambda max_steps=6: [{"step": 1, "coaching": "lift"}],
    )
    client = TestClient(granite_client.app)

    response = client.post("/racesight/coach-loop", json={"max_steps": 1})

    assert response.status_code == 200
    assert response.json() == {"steps": [{"step": 1, "coaching": "lift"}]}


def test_racesight_router_stream_endpoint_streams_text(monkeypatch) -> None:
    monkeypatch.setattr(
        "ai.orchestrator.routes.racesight_orchestrator",
        lambda message: f"stream:{message}",
    )
    client = TestClient(granite_client.app)

    response = client.post("/racesight/stream", json={"message": "hello"})

    assert response.status_code == 200
    assert "stream:hello" in response.text


def test_racesight_router_status_endpoint_returns_runtime_status(monkeypatch) -> None:
    monkeypatch.setattr(
        "ai.orchestrator.routes.get_runtime_status",
        lambda: {"status": "online", "summary": "Lap 7, P3"},
    )
    client = TestClient(granite_client.app)

    response = client.get("/racesight/status")

    assert response.status_code == 200
    assert response.json() == {"status": "online", "summary": "Lap 7, P3"}


def test_api_rejects_missing_api_key_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("RACESIGHT_API_KEY", "secret-token")
    client = TestClient(granite_client.app)

    response = client.post("/chat", json={"message": "hello"})

    assert response.status_code == 401


def test_api_accepts_bearer_api_key_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("RACESIGHT_API_KEY", "secret-token")
    monkeypatch.setattr(
        "ai.orchestrator.granite_client.racesight_orchestrator",
        lambda message: f"ok:{message}",
    )
    client = TestClient(granite_client.app)

    response = client.post(
        "/chat",
        json={"message": "hello"},
        headers={"Authorization": "Bearer secret-token"},
    )

    assert response.status_code == 200
    assert response.json() == {"response": "ok:hello"}
