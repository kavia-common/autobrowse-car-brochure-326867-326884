from __future__ import annotations

from fastapi import Header, HTTPException, status

from src.core.config import Settings


# PUBLIC_INTERFACE
def require_admin(settings: Settings, x_admin_key: str | None = Header(default=None)) -> None:
    """Admin auth dependency using a static API key.

    Contract:
      - If ADMIN_API_KEY is not set, admin endpoints are open (useful for local/demo).
      - If ADMIN_API_KEY is set, requests must provide header `X-Admin-Key` that matches.
      - Errors: raises 401 Unauthorized on mismatch.
    """
    if not settings.admin_api_key:
        return

    if not x_admin_key or x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin key",
        )
