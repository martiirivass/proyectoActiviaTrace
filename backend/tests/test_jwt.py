import uuid
from datetime import datetime, timedelta, timezone

import pytest
import jwt

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_2fa_token,
    decode_token,
    verify_token,
)

settings = get_settings()


class TestJWTFunctions:
    def test_create_access_token_returns_string(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, tenant_id=uuid.uuid4(), roles=["admin"])
        assert isinstance(token, str)
        assert len(token) > 50

    def test_create_access_token_contains_correct_claims(self):
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        roles = ["admin", "coordinator"]
        token = create_access_token(user_id=user_id, tenant_id=tenant_id, roles=roles)
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == str(user_id)
        assert payload["tenant_id"] == str(tenant_id)
        assert payload["roles"] == roles
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_access_token_expiry(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, tenant_id=uuid.uuid4(), roles=["user"])
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        assert now < exp
        diff = exp - now
        assert timedelta(minutes=14) < diff < timedelta(minutes=16)

    def test_create_refresh_token(self):
        user_id = uuid.uuid4()
        token = create_refresh_token(user_id=user_id, tenant_id=uuid.uuid4(), roles=["user"])
        assert isinstance(token, str)
        assert len(token) > 20
        assert isinstance(token, str)

    def test_create_2fa_token(self):
        user_id = uuid.uuid4()
        token = create_2fa_token(user_id=user_id, tenant_id=uuid.uuid4())
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "2fa"
        assert "tenant_id" in payload

    def test_create_2fa_token_expiry(self):
        user_id = uuid.uuid4()
        token = create_2fa_token(user_id=user_id, tenant_id=uuid.uuid4())
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        diff = exp - datetime.now(timezone.utc)
        assert timedelta(minutes=4) < diff < timedelta(minutes=6)

    def test_decode_token_valid(self):
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, tenant_id=tenant_id, roles=["admin"])
        payload = decode_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["tenant_id"] == str(tenant_id)
        assert payload["type"] == "access"

    def test_decode_token_invalid_signature(self):
        bad_token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.invalid"
        result = decode_token(bad_token)
        assert result is None

    def test_decode_token_expired(self):
        user_id = uuid.uuid4()
        import time
        from app.core.security import decode_token

        payload = {
            "sub": str(user_id),
            "type": "access",
            "tenant_id": str(uuid.uuid4()),
            "roles": [],
            "exp": int(time.time()) - 3600,
            "iat": int(time.time()) - 7200,
        }
        expired_token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
        result = decode_token(expired_token)
        assert result is None

    def test_verify_token_valid(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, tenant_id=uuid.uuid4(), roles=["user"])
        claims = verify_token(token, "access")
        assert claims is not None
        assert claims["sub"] == str(user_id)

    def test_verify_token_wrong_type(self):
        access_token = create_access_token(user_id=uuid.uuid4(), tenant_id=uuid.uuid4(), roles=["user"])
        claims = verify_token(access_token, "refresh")
        assert claims is None

    def test_verify_token_invalid(self):
        claims = verify_token("invalid.jwt.here", "access")
        assert claims is None

    def test_create_refresh_token_randomness(self):
        tokens = set()
        for _ in range(100):
            t = create_refresh_token(user_id=uuid.uuid4(), tenant_id=uuid.uuid4(), roles=["user"])
            tokens.add(t)
        assert len(tokens) == 100

    def test_access_token_different_each_time(self):
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        t1 = create_access_token(user_id=user_id, tenant_id=tenant_id, roles=["user"])
        t2 = create_access_token(user_id=user_id, tenant_id=tenant_id, roles=["user"])
        assert t1 != t2
