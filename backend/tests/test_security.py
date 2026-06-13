import base64
import os

import pytest

from app.core.security import EncryptionService, PasswordService


class TestPasswordService:
    def test_hash_returns_argon2id_string(self):
        hashed = PasswordService.hash("password123")
        assert hashed.startswith("$argon2id$")
        assert isinstance(hashed, str)
        assert len(hashed) > 20

    def test_verify_correct_password(self):
        hashed = PasswordService.hash("password123")
        assert PasswordService.verify("password123", hashed) is True

    def test_verify_incorrect_password(self):
        hashed = PasswordService.hash("password123")
        assert PasswordService.verify("wrong-password", hashed) is False

    def test_verify_empty_password(self):
        hashed = PasswordService.hash("password123")
        assert PasswordService.verify("", hashed) is False

    def test_hash_different_each_time(self):
        hash1 = PasswordService.hash("same-password")
        hash2 = PasswordService.hash("same-password")
        assert hash1 != hash2


class TestEncryptionService:
    def setup_method(self):
        self.service = EncryptionService(b"k" * 32)

    def test_encrypt_returns_different_string(self):
        result = self.service.encrypt("plaintext")
        assert result != "plaintext"
        assert isinstance(result, str)
        assert len(result) > 0

    def test_decrypt_returns_original(self):
        encrypted = self.service.encrypt("secret-data-123")
        decrypted = self.service.decrypt(encrypted)
        assert decrypted == "secret-data-123"

    def test_encrypt_different_each_time(self):
        result1 = self.service.encrypt("same-data")
        result2 = self.service.encrypt("same-data")
        assert result1 != result2

    def test_roundtrip_empty_string(self):
        encrypted = self.service.encrypt("")
        decrypted = self.service.decrypt(encrypted)
        assert decrypted == ""

    def test_roundtrip_unicode(self):
        original = "ñññ 🔑 test"
        encrypted = self.service.encrypt(original)
        decrypted = self.service.decrypt(encrypted)
        assert decrypted == original

    def test_tampered_ciphertext_raises_error(self):
        encrypted = self.service.encrypt("important-data")
        tampered = encrypted[:-1] + ("0" if encrypted[-1] != "0" else "1")
        with pytest.raises(Exception):
            self.service.decrypt(tampered)

    def test_from_settings_key(self):
        service = EncryptionService.from_settings_key("b" * 32)
        encrypted = service.encrypt("test")
        assert service.decrypt(encrypted) == "test"

    def test_invalid_key_length_raises_error(self):
        with pytest.raises(ValueError, match="exactly 32"):
            EncryptionService(b"short-key")

    def test_empty_ciphertext_raises_error(self):
        with pytest.raises(Exception):
            self.service.decrypt("")

    def test_decrypt_with_wrong_key(self):
        encrypted = self.service.encrypt("secret")
        other_service = EncryptionService(b"x" * 32)
        with pytest.raises(Exception):
            other_service.decrypt(encrypted)
