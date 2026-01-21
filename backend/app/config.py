"""Security configuration using pydantic-settings.

All sensitive values should be loaded from environment variables.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    api_title: str = "Zaoya API"
    api_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"  # development, staging, production

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database (for production - SQLAlchemy)
    database_url: Optional[str] = None

    # Security
    secret_key: str = "change-me-in-production"  # JWT secret
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    refresh_token_expire_days: int = 30

    # CORS (adjust for production)
    cors_origins: str = "*"  # Comma-separated list

    # Rate Limiting
    rate_limit_per_minute: int = 100
    rate_limit_per_hour: int = 1000

    # AI API Keys (default to GLM/智谱 AI)
    glm_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Google OAuth
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

    # Email (Resend or similar)
    email_api_key: Optional[str] = None
    email_from: str = "noreply@zaoya.app"
    email_from_name: str = "Zaoya"

    # Published Pages URL
    pages_url: str = "http://localhost:8000"  # Base URL for published pages

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()
