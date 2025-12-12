from typing import Final

API_TITLE: Final[str] = "Assignment02 API"
API_DESCRIPTION: Final[str] = "Async FastAPI application scaffold"
API_VERSION: Final[str] = "0.1.0"

# Rate limiting defaults
RATE_LIMIT_WINDOW_SECONDS: Final[float] = 5.0
RATE_LIMIT_WINDOW_MAX_REQUESTS: Final[int] = 10
RATE_LIMIT_MIN_INTERVAL: Final[float] = 0.5
BLACKLIST_DURATION: Final[float] = 10.0

