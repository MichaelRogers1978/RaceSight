from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from ai.orchestrator.control_loop import racesight_granite_call, racesight_orchestrator


app = FastAPI()


class ChatRequest(BaseModel):
	message: str


class GraniteRequest(BaseModel):
	prompt: str
	system_prompt: str | None = None


@app.post("/chat")
def chat(req: ChatRequest) -> dict[str, str]:
	result = racesight_orchestrator(req.message)
	return {"response": result}


@app.post("/granite")
def granite(req: GraniteRequest) -> dict[str, str]:
	result = racesight_granite_call(
		prompt=req.prompt,
		system_prompt=req.system_prompt,
	)
	return {"response": result}
