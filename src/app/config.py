from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: Optional[str] = None
    REDIS_URL: Optional[str] = None
    JWT_SECRET: str = "secret-for-dev"
    APP_ENV: str = "development"
    PEPPER: str = ""  # application-level secret pepper for password hashing

    model_config = ConfigDict(env_file=".env")


settings = Settings()
