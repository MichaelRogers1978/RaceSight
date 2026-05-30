from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque

from fastapi import HTTPException, Request, status


_DEFAULT_RATE_LIMIT_PER_MINUTE = 60
_DEFAULT_MAX_BODY_BYTES = 1_000_000


@dataclass(frozen=True)
class SecuritySettings:
	api_key: str | None
	rate_limit_per_minute: int
	max_body_bytes: int


_security_lock = threading.Lock()
_request_windows: dict[str, Deque[float]] = defaultdict(deque)


def load_security_settings() -> SecuritySettings:
	api_key = os.getenv("RACESIGHT_API_KEY", "").strip() or None
	try:
		rate_limit_per_minute = int(os.getenv("RACESIGHT_RATE_LIMIT_PER_MINUTE", str(_DEFAULT_RATE_LIMIT_PER_MINUTE)))
	except ValueError:
		rate_limit_per_minute = _DEFAULT_RATE_LIMIT_PER_MINUTE
	try:
		max_body_bytes = int(os.getenv("RACESIGHT_MAX_BODY_BYTES", str(_DEFAULT_MAX_BODY_BYTES)))
	except ValueError:
		max_body_bytes = _DEFAULT_MAX_BODY_BYTES
	return SecuritySettings(
		api_key=api_key,
		rate_limit_per_minute=max(1, rate_limit_per_minute),
		max_body_bytes=max(1, max_body_bytes),
	)


def _extract_client_id(request: Request) -> str:
	forwarded_for = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
	if forwarded_for:
		return forwarded_for
	client = request.client
	if client and client.host:
		return client.host
	return "unknown"


def enforce_api_key(request: Request, settings: SecuritySettings | None = None) -> None:
	settings = settings or load_security_settings()
	if not settings.api_key:
		return

	authorization = request.headers.get("authorization", "")
	bearer_token = ""
	if authorization.lower().startswith("bearer "):
		bearer_token = authorization.split(" ", 1)[1].strip()

	header_token = request.headers.get("x-racesight-token", "").strip()
	provided_token = bearer_token or header_token
	if not provided_token or provided_token != settings.api_key:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Missing or invalid API key",
		)


def enforce_rate_limit(request: Request, settings: SecuritySettings | None = None) -> None:
	settings = settings or load_security_settings()
	if settings.rate_limit_per_minute <= 0:
		return

	client_id = _extract_client_id(request)
	now = time.monotonic()
	window_start = now - 60.0

	with _security_lock:
		window = _request_windows[client_id]
		while window and window[0] < window_start:
			window.popleft()
		if len(window) >= settings.rate_limit_per_minute:
			raise HTTPException(
				status_code=status.HTTP_429_TOO_MANY_REQUESTS,
				detail="Rate limit exceeded",
			)
		window.append(now)


def enforce_request_size(request: Request, settings: SecuritySettings | None = None) -> None:
	settings = settings or load_security_settings()
	content_length = request.headers.get("content-length")
	if not content_length:
		return
	try:
		body_size = int(content_length)
	except ValueError:
		return
	if body_size > settings.max_body_bytes:
		raise HTTPException(
			status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
			detail="Request body too large",
		)