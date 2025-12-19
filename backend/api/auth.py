import os
import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import bcrypt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import select

try:
    from .models import ApiKey, User, get_session
except ImportError:  # Running as top-level module
    from models import ApiKey, User, get_session


SEC_HEADER = os.getenv("API_KEY_HEADER", "X-API-Key")
PEPPER = os.getenv("API_KEY_PEPPER", "")

# Primary envs (new)
JWT_SECRET = os.getenv("JWT_SECRET", os.getenv("JWT_HS256_SECRET", "change-me"))
JWT_ALGO = os.getenv("JWT_ALGO", os.getenv("JWT_ALG", "HS256"))
JWT_EXPIRE_MIN = int(os.getenv("JWT_EXPIRE_MIN", os.getenv("JWT_ACCESS_TTL_SECONDS", "60")))

# Optional issuer/audience (kept for backward compatibility)
JWT_ISS = os.getenv("JWT_ISS")
JWT_AUD = os.getenv("JWT_AUD")

security = HTTPBearer(auto_error=False)
optional_security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _401(msg: str = "Unauthorized"):
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, msg, headers={"WWW-Authenticate": "Bearer"})


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except ValueError:
        return False


def _build_options() -> dict:
    return {
        "verify_aud": bool(JWT_AUD),
        "verify_iss": bool(JWT_ISS),
    }


def mint_access_token(user_id: int, scopes: List[str]) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=JWT_EXPIRE_MIN)
    payload = {
        "sub": str(user_id),
        "scope": " ".join(scopes),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    user_fields = _USER_CONTEXT.get(user_id)
    if user_fields:
        payload.update(user_fields)
    if JWT_ISS:
        payload["iss"] = JWT_ISS
    if JWT_AUD:
        payload["aud"] = JWT_AUD
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGO],
        audience=JWT_AUD if JWT_AUD else None,
        issuer=JWT_ISS if JWT_ISS else None,
        options=_build_options(),
    )


def require_jwt(scopes: Optional[List[str]] = None):
    def _dep(cred: HTTPAuthorizationCredentials = Depends(security)):
        try:
            claims = decode_token(cred.credentials)
        except JWTError:
            _401("Invalid token")
        if scopes:
            have = set((claims.get("scope") or "").split())
            missing = [s for s in scopes if s not in have]
            if missing:
                raise HTTPException(status.HTTP_403_FORBIDDEN, f"Missing scopes: {missing}")
        return claims

    return _dep


def require_partner_token(scopes: Optional[List[str]] = None):
    jwt_dep = require_jwt(scopes)

    def _dep(cred: HTTPAuthorizationCredentials = Depends(security)):
        return jwt_dep(cred)

    return _dep


def require_api_key(
    x_api_key: str | None = Header(None, alias=SEC_HEADER),
    session=Depends(get_session),
) -> str:
    if not x_api_key:
        _401("Missing API key")
    records = session.exec(select(ApiKey).where(ApiKey.is_active == True)).all()
    for rec in records:
        if bcrypt.checkpw((PEPPER + x_api_key).encode(), rec.key_hash.encode()):
            return rec.name
    _401("Invalid API key")


def require_user_actor(scopes: Optional[List[str]] = None):
    jwt_dep = require_jwt(scopes)

    def _dep(
        cred: HTTPAuthorizationCredentials | None = Depends(optional_security),
        x_api_key: str | None = Header(None, alias=SEC_HEADER),
        session=Depends(get_session),
    ) -> str:
        if cred:
            claims = jwt_dep(cred)
            return str(claims.get("sub"))
        if x_api_key:
            return require_api_key(x_api_key=x_api_key, session=session)
        _401("Authorization header or API key required")

    return _dep


# Store contextual user fields (email/role) per token mint to include in payload
_USER_CONTEXT: dict[int, dict[str, str]] = {}


def create_access_token(user_id: int, email: str, role: str, scopes: Optional[List[str]] = None) -> str:
    # Stash context for inclusion when minting
    _USER_CONTEXT[user_id] = {"email": email, "role": role}
    try:
        return mint_access_token(user_id, scopes=scopes or [])
    finally:
        _USER_CONTEXT.pop(user_id, None)


def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(security),
    session=Depends(get_session),
) -> User:
    if not cred or cred.scheme.lower() != "bearer":
        _401("Missing or invalid Authorization header")
    try:
        claims = decode_token(cred.credentials)
        user_id = int(claims.get("sub", "0"))
    except (JWTError, ValueError):
        _401("Invalid token")
    user = session.get(User, user_id)
    if not user:
        _401("User not found")
    return user


# jose-compat aliases
create_access_token_legacy = mint_access_token
