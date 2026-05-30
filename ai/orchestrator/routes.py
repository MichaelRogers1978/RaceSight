from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ai.orchestrator.control_loop import (
    get_race_state,
    get_runtime_status,
    racesight_granite_call,
    racesight_orchestrator,
    racesight_race_engineer_brief,
    run_driver_coaching_loop,
    run_race_replay_mode,
    stream_text_chunks,
)


router = APIRouter(prefix="/racesight", tags=["racesight"])


class RaceSightRequest(BaseModel):
    message: str


class GraniteRequest(BaseModel):
    prompt: str
    system_prompt: str | None = None


class BriefRequest(BaseModel):
    focus: str = "balanced"


class ReplayRequest(BaseModel):
    max_frames: int = 6
    include_brief: bool = True


class CoachingLoopRequest(BaseModel):
    max_steps: int = 6


class StreamRequest(BaseModel):
    message: str


@router.post("")
def racesight_route(req: RaceSightRequest) -> dict[str, str]:
    return {"response": racesight_orchestrator(req.message)}


@router.post("/chat")
def racesight_chat(req: RaceSightRequest) -> dict[str, str]:
    return {"response": racesight_orchestrator(req.message)}


@router.post("/granite")
def racesight_granite(req: GraniteRequest) -> dict[str, str]:
    return {
        "response": racesight_granite_call(
            prompt=req.prompt,
            system_prompt=req.system_prompt,
        )
    }


@router.post("/brief")
def racesight_brief(req: BriefRequest) -> dict[str, object]:
    race_state = get_race_state()
    return racesight_race_engineer_brief(race_state, focus=req.focus)


@router.get("/status")
def racesight_status() -> dict[str, object]:
	return get_runtime_status()


@router.post("/replay")
def racesight_replay(req: ReplayRequest) -> dict[str, object]:
    return {"frames": run_race_replay_mode(max_frames=req.max_frames, include_brief=req.include_brief)}


@router.post("/coach-loop")
def racesight_coach_loop(req: CoachingLoopRequest) -> dict[str, object]:
    return {"steps": run_driver_coaching_loop(max_steps=req.max_steps)}


@router.post("/stream")
def racesight_stream(req: StreamRequest) -> StreamingResponse:
    text = racesight_orchestrator(req.message)
    return StreamingResponse(stream_text_chunks(text), media_type="text/plain; charset=utf-8")
