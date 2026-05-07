"""
FastAPI application entry point.
Wires routers, lifespan (DB init), CORS, and health check.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db
from app.routers import health, meetings, webhook


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables. Teardown: nothing (SQLite)."""
    init_db()
    yield


app = FastAPI(
    title="Meety",
    description="Bot de reuniones con IA — une Google Meet/Teams/Zoom, transcribe y resume.",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router, tags=["health"])
app.include_router(meetings.router, prefix="/meetings", tags=["meetings"])
app.include_router(webhook.router, prefix="/webhook", tags=["webhook"])
