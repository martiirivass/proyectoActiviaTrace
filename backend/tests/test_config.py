import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class TestSettings:
    def test_settings_loads_valid_env(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

        settings = get_settings()

        assert settings.database_url == "postgresql+asyncpg://user:pass@localhost:5432/db"
        assert settings.secret_key == "a" * 32
        assert settings.encryption_key == "b" * 32
        assert settings.access_token_expire_minutes == 30

    def test_settings_default_access_token_expire(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)

        settings = get_settings()

        assert settings.access_token_expire_minutes == 15

    def test_settings_fails_on_missing_database_url(self, monkeypatch):
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)
        monkeypatch.delenv("DATABASE_URL", raising=False)

        with pytest.raises(ValidationError) as exc_info:
            get_settings()

        assert "DATABASE_URL" in str(exc_info.value)

    def test_settings_fails_on_missing_secret_key(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)
        monkeypatch.delenv("SECRET_KEY", raising=False)

        with pytest.raises(ValidationError) as exc_info:
            get_settings()

        assert "SECRET_KEY" in str(exc_info.value)

    def test_settings_fails_on_missing_encryption_key(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.delenv("ENCRYPTION_KEY", raising=False)

        with pytest.raises(ValidationError) as exc_info:
            get_settings()

        assert "ENCRYPTION_KEY" in str(exc_info.value)

    def test_settings_fails_on_short_secret_key(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "short")
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)

        with pytest.raises(ValidationError) as exc_info:
            get_settings()

        assert "SECRET_KEY" in str(exc_info.value)

    def test_settings_fails_on_short_encryption_key(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "short")

        with pytest.raises(ValidationError) as exc_info:
            get_settings()

        assert "ENCRYPTION_KEY" in str(exc_info.value)

    def test_settings_fails_on_invalid_access_token_expire(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "not-a-number")

        with pytest.raises(ValidationError) as exc_info:
            get_settings()

        assert "ACCESS_TOKEN_EXPIRE_MINUTES" in str(exc_info.value)