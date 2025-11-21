from __future__ import annotations

from typing import Dict

from fastapi import Header, HTTPException, status

API_KEYS: Dict[str, str] = {
    "dev-key-123": "user1",
    "admin-key-456": "admin",
}


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    user = API_KEYS.get(x_api_key)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return user
