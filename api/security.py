"""
Shared-secret API key auth. Fine for a single-tenant internal tool;
swap for OAuth2/JWT (fastapi.security.OAuth2PasswordBearer) if you need
per-user identity later.
"""
from fastapi import Header, HTTPException, status
from api.config import get_settings


def require_api_key(x_api_key: str = Header(default=None)):
    settings = get_settings()
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing or invalid X-API-Key header")
    return True