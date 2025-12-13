from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional
from enum import StrEnum

class StorageKind(StrEnum):
    FS = "fs"
    DB = "db"

class Settings(BaseSettings):
    DATABASE_URL: Optional[str] = None
    REDIS_URL: Optional[str] = None
    JWT_SECRET: str = "secret-for-dev"
    APP_ENV: str = "development"
    # application-level secret pepper for password hashing; required for security
    PEPPER: str  # required; set via environment or .env

    # storage selection: 'fs' stores files on filesystem, 'db' stores blobs inline
    STORAGE_KIND: StorageKind = StorageKind.FS

    model_config = ConfigDict(env_file=".env")


settings = Settings()
