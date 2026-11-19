from typing import Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings

# Development-only placeholder. Rejected outside ENVIRONMENT=development.
DEFAULT_SECRET_KEY = "CHANGE-ME-IN-PRODUCTION"  # noqa: S105  # nosec B105
MIN_SECRET_KEY_LENGTH = 32


class Settings(BaseSettings):
    PROJECT_NAME: str = "SecureOps"
    VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "test", "staging", "production"] = "development"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+asyncpg://secureops:secureops@localhost:5432/secureops"
    DATABASE_ECHO: bool = False

    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = DEFAULT_SECRET_KEY
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    ALGORITHM: str = "HS256"

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    EVIDENCE_STORAGE_BACKEND: str = "local"  # local | azure_blob | s3
    EVIDENCE_STORAGE_PATH: str = "./evidence-store"
    EVIDENCE_MAX_UPLOAD_MB: int = 50

    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    PROWLER_DOCKER_IMAGE: str = "prowler/prowler:latest"
    TRIVY_DOCKER_IMAGE: str = "aquasec/trivy:latest"

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    OPENTELEMETRY_ENABLED: bool = False
    OTLP_ENDPOINT: str = "http://localhost:4317"

    model_config = {"env_prefix": "SECUREOPS_", "env_file": ".env", "case_sensitive": True}

    @model_validator(mode="after")
    def _require_strong_secret_outside_dev(self) -> Self:
        if self.ENVIRONMENT in ("development", "test"):
            return self
        if self.SECRET_KEY == DEFAULT_SECRET_KEY or len(self.SECRET_KEY) < MIN_SECRET_KEY_LENGTH:
            raise ValueError(
                f"SECRET_KEY must be set to a random value of at least "
                f"{MIN_SECRET_KEY_LENGTH} characters when ENVIRONMENT={self.ENVIRONMENT}"
            )
        return self


settings = Settings()
