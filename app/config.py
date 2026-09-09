import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "GuardWAF"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Database Configuration (PostgreSQL default, SQLite fallback for unit tests)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./waf_governance.db")

    def get_normalized_database_url(self) -> str:
        if self.DATABASE_URL.startswith("postgres://"):
            return self.DATABASE_URL.replace("postgres://", "postgresql://", 1)
        return self.DATABASE_URL

    # Rules & Security Configuration
    RULES_PATH: str = os.getenv("RULES_PATH", "rules.yaml")
    SHADOW_MODE_GLOBAL: bool = os.getenv("SHADOW_MODE_GLOBAL", "false").lower() == "true"

    # LLM Provider Keys & Endpoints (OpenAI-compatible xAI Grok default)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.x.ai/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "grok-2")

    class Config:
        env_file = ".env"


settings = Settings()
if settings.DATABASE_URL.startswith("postgres://"):
    settings.DATABASE_URL = settings.DATABASE_URL.replace("postgres://", "postgresql://", 1)
