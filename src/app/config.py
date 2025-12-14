from enum import StrEnum
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class StorageKind(StrEnum):
    FS = "fs"
    DB = "db"

class Settings(BaseSettings):
    DATABASE_URL: Optional[str] = None
    REDIS_URL: Optional[str] = None
    JWT_SECRET: str = "secret-for-dev"
    APP_ENV: str = "development"
    # application-level secret pepper for password hashing; required for security
    PEPPER: str = "test-pepper"

    # storage selection: 'fs' stores files on filesystem, 'db' stores blobs inline
    STORAGE_KIND: StorageKind = StorageKind.FS

    # Comma-separated list of allowed CORS origins. Example:
    # CORS_ORIGINS=http://localhost:3000,https://example.com
    CORS_ORIGINS: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins(self) -> list[str]:
        """Return parsed list of origins. Empty list disables CORS middleware."""
        if not self.CORS_ORIGINS:
            return []
        return [s.strip() for s in self.CORS_ORIGINS.split(",") if s.strip()]

settings = Settings()
