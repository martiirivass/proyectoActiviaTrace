import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class TestSettings:
    def _make_settings(self, monkeypatch, env_vars: dict[str, str], **kwargs):
        for k, v in env_vars.items():
            monkeypatch.setenv(k, v)
        for k in ("DATABASE_URL", "SECRET_KEY", "ENCRYPTION_KEY"):
            if k not in env_vars:
                monkeypatch.delenv(k, raising=False)
        return Settings(_env_file=None, **kwargs)

    def test_settings_loads_valid_env(self, monkeypatch):
        settings = self._make_settings(monkeypatch, {
            "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/db",
            "SECRET_KEY": "a" * 32,
            "ENCRYPTION_KEY": "b" * 32,
            "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        })

        assert settings.database_url == "postgresql+asyncpg://user:pass@localhost:5432/db"
        assert settings.secret_key == "a" * 32
        assert settings.encryption_key == "b" * 32
        assert settings.access_token_expire_minutes == 30

    def test_settings_default_access_token_expire(self, monkeypatch):
        settings = self._make_settings(monkeypatch, {
            "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/db",
            "SECRET_KEY": "a" * 32,
            "ENCRYPTION_KEY": "b" * 32,
        })

        assert settings.access_token_expire_minutes == 15

    def test_settings_fails_on_missing_database_url(self, monkeypatch):
        with pytest.raises(ValidationError) as exc_info:
            self._make_settings(monkeypatch, {
                "SECRET_KEY": "a" * 32,
                "ENCRYPTION_KEY": "b" * 32,
            })

        assert "DATABASE_URL" in str(exc_info.value)

    def test_settings_fails_on_missing_secret_key(self, monkeypatch):
        with pytest.raises(ValidationError) as exc_info:
            self._make_settings(monkeypatch, {
                "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/db",
                "ENCRYPTION_KEY": "b" * 32,
            })

        assert "SECRET_KEY" in str(exc_info.value)

    def test_settings_fails_on_missing_encryption_key(self, monkeypatch):
        with pytest.raises(ValidationError) as exc_info:
            self._make_settings(monkeypatch, {
                "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/db",
                "SECRET_KEY": "a" * 32,
            })

        assert "ENCRYPTION_KEY" in str(exc_info.value)

    def test_settings_fails_on_short_secret_key(self, monkeypatch):
        with pytest.raises(ValidationError) as exc_info:
            self._make_settings(monkeypatch, {
                "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/db",
                "SECRET_KEY": "short",
                "ENCRYPTION_KEY": "b" * 32,
            })

        assert "SECRET_KEY" in str(exc_info.value)

    def test_settings_fails_on_short_encryption_key(self, monkeypatch):
        with pytest.raises(ValidationError) as exc_info:
            self._make_settings(monkeypatch, {
                "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/db",
                "SECRET_KEY": "a" * 32,
                "ENCRYPTION_KEY": "short",
            })

        assert "ENCRYPTION_KEY" in str(exc_info.value)

    def test_settings_fails_on_invalid_access_token_expire(self, monkeypatch):
        with pytest.raises(ValidationError) as exc_info:
            self._make_settings(monkeypatch, {
                "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/db",
                "SECRET_KEY": "a" * 32,
                "ENCRYPTION_KEY": "b" * 32,
                "ACCESS_TOKEN_EXPIRE_MINUTES": "not-a-number",
            })

        assert "ACCESS_TOKEN_EXPIRE_MINUTES" in str(exc_info.value)