"""Health check endpoint."""

from fastapi import APIRouter

from app.config import settings
from app.models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        vexa_configured=bool(settings.VEXA_API_KEY),
        openrouter_configured=bool(settings.OPENROUTER_API_KEY),
        database="sqlite",
    )
