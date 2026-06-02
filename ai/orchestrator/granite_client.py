from __future__ import annotations

import os
from pathlib import Path

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ai.orchestrator.control_loop import get_race_state, racesight_granite_call, racesight_orchestrator
from ai.orchestrator.routes import router as racesight_router
from ai.orchestrator.security import enforce_api_key, enforce_rate_limit, enforce_request_size


app = FastAPI()
app.include_router(racesight_router)


@app.exception_handler(RuntimeError)
async def handle_runtime_error(_request: Request, exc: RuntimeError) -> JSONResponse:
	return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.exception_handler(ValueError)
async def handle_value_error(_request: Request, exc: ValueError) -> JSONResponse:
	return JSONResponse(status_code=400, content={"detail": str(exc)})


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
		return await call_next(request)
	except RuntimeError as exc:
		return JSONResponse(status_code=502, content={"detail": str(exc)})
	except ValueError as exc:
		return JSONResponse(status_code=400, content={"detail": str(exc)})
	except Exception as exc:
		status_code = getattr(exc, "status_code", 500)
		detail = getattr(exc, "detail", "Request rejected")
		return JSONResponse(status_code=status_code, content={"detail": detail})


class ChatRequest(BaseModel):
	message: str


class GraniteRequest(BaseModel):
	prompt: str
	system_prompt: str | None = None


def _local_pit_fallback_message(message: str) -> str:
	race_state = get_race_state()
	race_context = race_state.get("race_context", {})
	pit = race_state.get("pit_strategy_model", {})
	safety = race_state.get("safety_status", {})

	lap = race_context.get("race_lap", "n/a")
	position = race_context.get("position_overall", "n/a")
	should_pit = pit.get("should_pit_now", False)
	window = pit.get("recommended_pit_window", {})
	window_start = window.get("start_lap", "n/a")
	window_end = window.get("end_lap", "n/a")
	confidence = pit.get("confidence", "n/a")
	alert_level = safety.get("alert_level", "none")
	message_text = message.lower()

	if "rain" in message_text:
		if should_pit:
			action = "Rain is coming soon, so box now if the lane is clear and you can switch before the grip drops."
		else:
			action = "Stay out for the next few minutes, then pit just before the rain arrives to avoid an extra stop on slick tires."
		return (
			f"Lap {lap}, P{position}, safety {alert_level}. "
			f"Rain strategy: target laps {window_start}-{window_end}, confidence {confidence}. "
			+ action
		)

	if should_pit:
		action = "Pit this lap if traffic release is clear and no sudden yellow emerges."
	else:
		action = "Stay out for now and target the recommended pit window."

	return (
		f"Lap {lap}, P{position}, safety {alert_level}. "
		f"Recommended pit window: laps {window_start}-{window_end}, confidence {confidence}. "
		+ action
	)


@app.post("/chat")
def chat(req: ChatRequest) -> dict[str, str]:
	try:
		result = racesight_orchestrator(req.message)
	except RuntimeError:
		result = _local_pit_fallback_message(req.message)
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
