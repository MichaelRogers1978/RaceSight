from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ai.orchestrator.control_loop import racesight_granite_call, racesight_orchestrator
from ai.orchestrator.routes import router as racesight_router
from ai.orchestrator.security import enforce_api_key, enforce_rate_limit, enforce_request_size


app = FastAPI()
app.include_router(racesight_router)


@app.middleware("http")
async def protect_api(request: Request, call_next):
	try:
		enforce_request_size(request)
		enforce_api_key(request)
		enforce_rate_limit(request)
	except Exception as exc:
		status_code = getattr(exc, "status_code", 500)
		detail = getattr(exc, "detail", "Request rejected")
		return JSONResponse(status_code=status_code, content={"detail": detail})
	return await call_next(request)


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
