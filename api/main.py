"""
FastAPI entrypoint.
    uvicorn api.main:api --reload --host 0.0.0.0 --port 8001
"""
import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

import logger_setup
from api.config import get_settings
from api.routers import reports, jobs, data, health

log = logger_setup.get_logger(__name__)
settings = get_settings()

app = FastAPI(title="Report Generator API", version="2.0.0",
              description="Trigger, track, and retrieve automated sales reports")

app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                    allow_methods=["*"], allow_headers=["*"])

# Simple in-memory sliding-window rate limiter, keyed by client IP.
# For multi-replica deployments, replace with a Redis-backed limiter so
# limits are shared across instances.
_rate_state: dict[str, list[float]] = {}


@app.middleware("http")
async def rate_limit_and_log(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    window = _rate_state.setdefault(client_ip, [])
    window[:] = [t for t in window if now - t < 60]
    if len(window) >= settings.rate_limit_per_minute:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
    window.append(now)

    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    log.info(f"[{request_id}] {request.method} {request.url.path} -> {response.status_code} ({elapsed:.1f}ms)")
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    log.error(f"Unhandled exception on {request.url.path}: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(health.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(data.router, prefix="/api/v1")