from __future__ import annotations

from types import SimpleNamespace

from ai.orchestrator import control_loop


def test_control_loop_calls_loaded_orchestrator(monkeypatch) -> None:
    fake_module = SimpleNamespace(racesight_orchestrator=lambda message: f"ok:{message}")
    monkeypatch.setattr(control_loop, "_ORCHESTRATOR_MODULE", fake_module)

    result = control_loop.racesight_orchestrator("hello")

    assert result == "ok:hello"
