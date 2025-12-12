from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from enum import Enum
from typing import Optional

class FileStorageOption(str, Enum):
    db = "db"
    filesystem = "filesystem"
    s3 = "s3"

class Settings(BaseSettings):
    DATABASE_URL: Optional[str] = None
    REDIS_URL: Optional[str] = None
    JWT_SECRET: str = "secret-for-dev"
    FILE_STORAGE: FileStorageOption = FileStorageOption.db  # options validated via enum
    APP_ENV: str = "development"

    model_config = ConfigDict(env_file=".env")

settings = Settings()
