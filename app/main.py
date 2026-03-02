"""FastAPI app: triage API. Tenant-aware; multi-tenant True Commerce."""

import logging
import os

import logfire
from fastapi import FastAPI

from app.api.triage import router as triage_router

# LOG_LEVEL=DEBUG to see agent calls and per-item debug logs (default INFO)
logging.basicConfig(
    level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
)

# Only require auth when sending to Logfire; local dev works without `logfire auth`.
logfire.configure(send_to_logfire="if-token-present")
logfire.instrument_pydantic_ai()

app = FastAPI(
    title="True Commerce Triage Agent",
    description="Intelligent event monitoring and triage; batch error classification and remediation (multi-tenant).",
    version="0.1.0",
)
logfire.instrument_fastapi(app)
app.include_router(triage_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
