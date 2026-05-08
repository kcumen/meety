from fastapi import Header, HTTPException, Depends
from app.config import settings

async def verify_api_key(
    x_meety_api_key: str = Header(None),
    key: str = None
):
    """
    Dependency to verify the Meety API Key.
    Supports Header (for fetch) and Query Param (for SSE).
    """
    if not settings.MEETY_API_KEY:
        return
    
    token = x_meety_api_key or key
    
    if token != settings.MEETY_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")
