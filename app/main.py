"""FastAPI app: triage API. Tenant-aware; multi-tenant True Commerce."""

from fastapi import FastAPI
from app.api.triage import router as triage_router

app = FastAPI(
    title="True Commerce Triage Agent",
    description="Intelligent event monitoring and triage; batch error classification and remediation (multi-tenant).",
    version="0.1.0",
)
app.include_router(triage_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
