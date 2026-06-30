"""Tests for Bubble token verification."""
from __future__ import annotations

import pytest
from fastapi import HTTPException
from jose import jwt
from unittest.mock import patch

from app.core.auth import CurrentUser, _decode_token, require_admin, require_reviewer


SECRET = "test-secret-key"


def _make_token(payload: dict, secret: str = SECRET) -> str:
    return jwt.encode(payload, secret, algorithm="HS256")


class TestDecodeToken:
    def test_valid_token_with_secret(self):
        token = _make_token({"sub": "user123", "role": "appraiser", "email": "a@b.com"})
        with patch("app.core.auth.settings") as mock_settings:
            mock_settings.bubble_auth_secret = SECRET
            claims = _decode_token(token)
        assert claims["sub"] == "user123"
        assert claims["role"] == "appraiser"

    def test_invalid_secret_raises(self):
        token = _make_token({"sub": "user123"}, secret="wrong")
        with patch("app.core.auth.settings") as mock_settings:
            mock_settings.bubble_auth_secret = SECRET
            from jose import JWTError
            with pytest.raises(JWTError):
                _decode_token(token)

    def test_dev_mode_no_verification(self):
        """When bubble_auth_secret is empty string, skip verification."""
        token = _make_token({"sub": "dev-user", "role": "admin"})
        with patch("app.core.auth.settings") as mock_settings:
            mock_settings.bubble_auth_secret = ""
            claims = _decode_token(token)
        assert claims["sub"] == "dev-user"


class TestCurrentUser:
    def test_is_appraiser(self):
        u = CurrentUser(user_id="u1", role="appraiser")
        assert u.is_appraiser
        assert not u.is_reviewer
        assert not u.is_admin

    def test_reviewer_passes_is_reviewer(self):
        u = CurrentUser(user_id="u1", role="reviewer")
        assert u.is_reviewer
        assert not u.is_admin

    def test_admin_passes_both(self):
        u = CurrentUser(user_id="u1", role="admin")
        assert u.is_reviewer
        assert u.is_admin


class TestRoleGuards:
    def test_require_reviewer_blocks_appraiser(self):
        u = CurrentUser(user_id="u1", role="appraiser")
        with pytest.raises(HTTPException) as exc_info:
            require_reviewer(u)
        assert exc_info.value.status_code == 403

    def test_require_reviewer_allows_reviewer(self):
        u = CurrentUser(user_id="u1", role="reviewer")
        result = require_reviewer(u)
        assert result.role == "reviewer"

    def test_require_admin_blocks_reviewer(self):
        u = CurrentUser(user_id="u1", role="reviewer")
        with pytest.raises(HTTPException) as exc_info:
            require_admin(u)
        assert exc_info.value.status_code == 403

    def test_require_admin_allows_admin(self):
        u = CurrentUser(user_id="u1", role="admin")
        result = require_admin(u)
        assert result.role == "admin"
