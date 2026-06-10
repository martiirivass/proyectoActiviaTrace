from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    database_url: str = Field(..., alias="DATABASE_URL")
    database_url_test: str | None = Field(default=None, alias="DATABASE_URL_TEST")
    secret_key: str = Field(..., alias="SECRET_KEY", min_length=32)
    encryption_key: str = Field(..., alias="ENCRYPTION_KEY", min_length=32, max_length=32)
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=30, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    two_fa_token_expire_minutes: int = Field(default=5, alias="2FA_TOKEN_EXPIRE_MINUTES")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    otel_exporter_otlp_endpoint: str | None = Field(default=None, alias="OTEL_EXPORTER_OTLP_ENDPOINT")
    otel_service_name: str = Field(default="activia-trace-api", alias="OTEL_SERVICE_NAME")
    moodle_enabled: bool = Field(default=False, alias="MOODLE_ENABLED")
    moodle_url: str = Field(default="", alias="MOODLE_URL")
    moodle_token: str = Field(default="", alias="MOODLE_TOKEN")
    moodle_timeout: int = Field(default=30, alias="MOODLE_TIMEOUT")

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key_length(cls, v: str) -> str:
        if len(v) != 32:
            raise ValueError("ENCRYPTION_KEY must be exactly 32 characters")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()