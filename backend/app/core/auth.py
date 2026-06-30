"""
Bubble token verification.

Bubble passes a JWT-style token in the Authorization: Bearer header.
We verify the token signature using BUBBLE_AUTH_SECRET, then extract
user_id and role claims.

In dev (no secret set), token is decoded without verification for local testing.
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings

bearer_scheme = HTTPBearer()


def _decode_token(token: str) -> dict:
    if settings.bubble_auth_secret:
        return jwt.decode(
            token,
            settings.bubble_auth_secret,
            algorithms=["HS256"],
        )
    # Dev mode — no secret configured, skip verification
    return jwt.get_unverified_claims(token)


class CurrentUser:
    def __init__(self, user_id: str, role: str, email: str = ""):
        self.user_id = user_id
        self.role = role
        self.email = email

    @property
    def is_appraiser(self) -> bool:
        return self.role == "appraiser"

    @property
    def is_reviewer(self) -> bool:
        return self.role in ("reviewer", "admin")

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> CurrentUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        claims = _decode_token(credentials.credentials)
        user_id: str = claims.get("sub") or claims.get("user_id")
        role: str = claims.get("role", "appraiser")
        email: str = claims.get("email", "")
        if not user_id:
            raise credentials_exception
        return CurrentUser(user_id=user_id, role=role, email=email)
    except JWTError:
        raise credentials_exception


def require_reviewer(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    if not user.is_reviewer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Reviewer access required")
    return user


def require_admin(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
