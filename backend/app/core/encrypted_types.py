import sqlalchemy.types as types
from app.core.security import EncryptionService
from app.core.config import get_settings


class EncryptedString(types.TypeDecorator):
    impl = types.String
    cache_ok = True

    def __init__(self, length=500, **kwargs):
        super().__init__(length=length, **kwargs)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        settings = get_settings()
        svc = EncryptionService.from_settings_key(settings.encryption_key)
        return svc.encrypt(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        settings = get_settings()
        svc = EncryptionService.from_settings_key(settings.encryption_key)
        return svc.decrypt(value)
