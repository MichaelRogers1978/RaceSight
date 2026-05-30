from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ai.orchestrator.control_loop import racesight_granite_call, racesight_orchestrator


router = APIRouter(prefix="/racesight", tags=["racesight"])


class RaceSightRequest(BaseModel):
    message: str


class GraniteRequest(BaseModel):
    prompt: str
    system_prompt: str | None = None


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
