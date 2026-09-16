"""
app/main.py

Entry point. Run locally with:
    uvicorn app.main:app --reload

Then open http://localhost:8000/docs for interactive API docs.
"""

from fastapi import FastAPI

from app.routers import drivers, sessions

app = FastAPI(
    title="GridWatch",
    description="Mock racing telemetry API for testing AI-assisted QA automation.",
    version="0.1.0",
)

app.include_router(drivers.router)
app.include_router(sessions.router)


@app.get("/health", tags=["meta"])
def health_check():
    """Simple liveness check — useful in CI to confirm the app boots."""
    return {"status": "ok"}
