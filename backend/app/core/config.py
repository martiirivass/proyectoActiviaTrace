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
    otel_exporter_otlp_endpoint: str | None = Field(default=None, alias="OTEL_EXPORTER_OTLP_ENDPOINT")
    otel_service_name: str = Field(default="activia-trace-api", alias="OTEL_SERVICE_NAME")

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key_length(cls, v: str) -> str:
        if len(v) != 32:
            raise ValueError("ENCRYPTION_KEY must be exactly 32 characters")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()