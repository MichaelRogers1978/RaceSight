from __future__ import annotations

import os
from pathlib import Path

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ai.orchestrator.control_loop import racesight_granite_call, racesight_orchestrator
from ai.orchestrator.routes import router as racesight_router
from ai.orchestrator.security import enforce_api_key, enforce_rate_limit, enforce_request_size


app = FastAPI()
app.include_router(racesight_router)


def _load_cors_allow_origins() -> list[str]:
	raw_value = os.getenv("RACESIGHT_CORS_ALLOW_ORIGINS", "").strip()
	if raw_value:
		return [origin.strip() for origin in raw_value.split(",") if origin.strip()]
	return ["http://127.0.0.1:8000", "http://localhost:8000"]


app.add_middleware(
	CORSMiddleware,
	allow_origins=_load_cors_allow_origins(),
	allow_credentials=False,
	allow_methods=["GET", "POST", "OPTIONS"],
	allow_headers=["*"],
)


@app.middleware("http")
async def protect_api(request: Request, call_next):
	if request.method == "OPTIONS":
		return await call_next(request)
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


frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
