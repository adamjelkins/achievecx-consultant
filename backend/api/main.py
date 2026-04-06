"""
api/main.py

FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from api.routes import (
    sessions,
    inference,
    conversation,
    assessment,
    risk,
    business_case,
    blueprint,
    vendors,
    debug,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    print(f"[achievecx] Starting in {settings.app_env} mode")
    yield
    print("[achievecx] Shutting down")


app = FastAPI(
    title="AchieveCX AI Consultant API",
    version="2.0.0",
    description="CX architecture design platform — FastAPI backend",
    lifespan=lifespan,
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ──
app.include_router(sessions.router,      prefix="/api/sessions",      tags=["Sessions"])
app.include_router(inference.router,     prefix="/api/inference",     tags=["Inference"])
app.include_router(conversation.router,  prefix="/api/conversation",  tags=["Conversation"])
app.include_router(assessment.router,    prefix="/api/assessment",    tags=["Assessment"])
app.include_router(risk.router,          prefix="/api/risk",          tags=["Risk"])
app.include_router(business_case.router, prefix="/api/business-case", tags=["Business Case"])
app.include_router(blueprint.router,     prefix="/api/blueprint",     tags=["Blueprint"])
app.include_router(vendors.router,       prefix="/api/vendors",       tags=["Vendors"])

# Debug routes — dev only
if settings.app_env != "production":
    app.include_router(debug.router, prefix="/api/debug", tags=["Debug"])


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}