import uuid

from pydantic import BaseModel, ConfigDict, EmailStr


class CurrentUser(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    email: str
    tenant_id: uuid.UUID
    roles: list[str]


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str


class LoginResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str | None = None
    expires_in: int | None = None
    requires_2fa: bool = False
    two_fa_token: str | None = None


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str


class RefreshResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class TwoFAEnrolResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    secret: str
    uri: str
    qr_code: str


class TwoFAVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    two_fa_token: str
    totp_code: str


class TwoFADisableRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password: str


class ForgotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str


class ResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str
    new_password: str
