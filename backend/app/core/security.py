import base64
import os

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


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
