import base64
import hashlib
import os
import secrets
import time
import uuid

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import jwt as jose_jwt

from app.core.config import get_settings

settings = get_settings()


def create_access_token(user_id: uuid.UUID, tenant_id: uuid.UUID, roles: list[str]) -> str:
    payload = {
        "jti": str(uuid.uuid4()),
        "sub": str(user_id),
        "type": "access",
        "tenant_id": str(tenant_id),
        "roles": roles,
        "iat": int(time.time()),
        "exp": int(time.time()) + settings.access_token_expire_minutes * 60,
    }
    return jose_jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: uuid.UUID, tenant_id: uuid.UUID, roles: list[str]) -> str:
    return secrets.token_urlsafe(64)


def create_2fa_token(user_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    payload = {
        "sub": str(user_id),
        "type": "2fa",
        "tenant_id": str(tenant_id),
        "iat": int(time.time()),
        "exp": int(time.time()) + settings.two_fa_token_expire_minutes * 60,
    }
    return jose_jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict | None:
    try:
        payload = jose_jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except jose_jwt.JWTError:
        return None


def verify_token(token: str, expected_type: str) -> dict | None:
    payload = decode_token(token)
    if payload is None:
        return None
    if payload.get("type") != expected_type:
        return None
    return payload


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class PasswordService:
    _hasher = PasswordHasher()

    @classmethod
    def hash(cls, password: str) -> str:
        return cls._hasher.hash(password)

    @classmethod
    def verify(cls, password: str, hash: str) -> bool:
        try:
            return cls._hasher.verify(hash, password)
        except VerifyMismatchError:
            return False


class EncryptionService:
    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("Encryption key must be exactly 32 bytes")
        self._aesgcm = AESGCM(key)

    @classmethod
    def from_settings_key(cls, key_str: str) -> "EncryptionService":
        return cls(key_str.encode("utf-8"))

    def encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(12)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(nonce + ciphertext).decode("utf-8")

    def decrypt(self, encrypted: str) -> str:
        data = base64.b64decode(encrypted)
        nonce = data[:12]
        ciphertext = data[12:]
        plaintext = self._aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
