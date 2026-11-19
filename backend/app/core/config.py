from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "SecureOps"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+asyncpg://secureops:secureops@localhost:5432/secureops"
    DATABASE_ECHO: bool = False

    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION"
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


settings = Settings()
