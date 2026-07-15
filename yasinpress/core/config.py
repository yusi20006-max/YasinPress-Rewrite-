"""Core settings model."""
from dataclasses import dataclass
import os
from .constants import DEFAULT_DATABASE_PATH

@dataclass(frozen=True)
class Settings:
    """Typed application settings."""
    environment: str = "production"
    database_path: str = DEFAULT_DATABASE_PATH
    log_level: str = "INFO"
    secret_key: str = "change-me"

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from environment variables."""
        return cls(
            environment=os.getenv("YASINPRESS_ENV", cls.environment),
            database_path=os.getenv("YASINPRESS_DATABASE_PATH", cls.database_path),
            log_level=os.getenv("YASINPRESS_LOG_LEVEL", cls.log_level),
            secret_key=os.getenv("YASINPRESS_SECRET_KEY", cls.secret_key),
        )
