import json
import logging
import re
import time
from collections import defaultdict, deque
from threading import Lock
from uuid import uuid4
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import StaleDataError
from app.api.routes import requests, operations, tools
from app.core.config import settings
from app.security.body_limit import BodyLimitMiddleware
from app.integrations.microsoft.providers import ProviderError

app = FastAPI(title="AssessFlow API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings().cors_origins.split(","),
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Demo-User",
        "Idempotency-Key",
        "X-Correlation-ID",
        "X-Graph-Token",
    ],
    expose_headers=["X-Correlation-ID"],
)
logger = logging.getLogger("assessflow")
logging.basicConfig(level=logging.INFO)
for noisy_logger in ["httpx", "httpx2", "azure"]:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)
windows = defaultdict(deque)
rate_lock = Lock()


@app.middleware("http")
async def observability(request: Request, call_next):
    supplied = request.headers.get("X-Correlation-ID", "")
    request.state.correlation_id = (
        supplied if re.fullmatch(r"[A-Za-z0-9-]{8,80}", supplied) else str(uuid4())
    )
    started = time.perf_counter()
    host = request.client.host if request.client else "unknown"
    with rate_lock:
        current = time.monotonic()
        queue = windows[host]
        while queue and queue[0] < current - 60:
            queue.popleft()
        limited = len(queue) >= 120 and request.method != "OPTIONS"
        if not limited and request.method != "OPTIONS":
            queue.append(current)
        if len(windows) > 10000:
            for key in list(windows):
                if not windows[key] or windows[key][-1] < current - 60:
                    del windows[key]
    if limited:
        response = JSONResponse(
            {
                "error": {
                    "code": "rate_limited",
                    "message": "Too many requests",
                    "correlation_id": request.state.correlation_id,
                }
            },
            status_code=429,
            headers={"Retry-After": "60"},
        )
    elif len(await request.body()) > 200000:
        response = JSONResponse(
            {"error": {"code": "payload_too_large", "message": "Payload limit is 200KB"}},
            status_code=413,
        )
    else:
        response = await call_next(request)
    response.headers["X-Correlation-ID"] = request.state.correlation_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    logger.info(
        json.dumps(
            {
                "event": "http_request",
                "method": request.method,
                "route": request.scope.get("route").path
                if request.scope.get("route")
                else "unmatched",
                "status": response.status_code,
                "latency_ms": round((time.perf_counter() - started) * 1000),
                "correlation_id": request.state.correlation_id,
                "provider_mode": settings().assessflow_mode,
            }
        )
    )
    return response


def error(request, status, code, message):
    return JSONResponse(
        {
            "error": {
                "code": code,
                "message": message,
                "correlation_id": getattr(request.state, "correlation_id", "unknown"),
            }
        },
        status_code=status,
    )


@app.exception_handler(HTTPException)
async def http_error(request, exc):
    return error(request, exc.status_code, "request_rejected", str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return error(request, 422, "validation_error", "Input does not match the API contract")


@app.exception_handler(ProviderError)
async def provider_error(request, exc):
    return error(request, 503, "provider_unavailable", str(exc))


@app.exception_handler(IntegrityError)
@app.exception_handler(StaleDataError)
async def conflict_error(request, exc):
    return error(
        request, 409, "concurrent_update", "Concurrent or duplicate update; reload and retry"
    )


@app.exception_handler(OperationalError)
async def database_error(request, exc):
    return error(request, 503, "database_unavailable", "Database temporarily unavailable")


@app.exception_handler(Exception)
async def internal_error(request, exc):
    logger.error(
        json.dumps(
            {
                "event": "internal_error",
                "class": type(exc).__name__,
                "correlation_id": getattr(request.state, "correlation_id", "unknown"),
            }
        )
    )
    return error(request, 500, "internal_error", "Unexpected server error")


@app.get("/health")
def health() -> dict:
    return {"status": "alive", "mode": settings().assessflow_mode}


@app.get("/ready")
def ready():
    from app.db.session import SessionLocal
    from sqlalchemy import text

    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {"status": "ready"}


app.include_router(requests.router)
app.include_router(operations.router)
app.include_router(tools.router)

app.add_middleware(BodyLimitMiddleware)
