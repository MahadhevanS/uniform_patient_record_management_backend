from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, computed_field
from typing import Optional

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables (.env file).
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # --- Database Settings ---
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "patient_db"

    @computed_field
    @property
    def DATABASE_URL(self) -> PostgresDsn:
        """Computes the full PostgreSQL URL for SQLAlchemy."""
        return PostgresDsn.build(
            scheme="postgresql",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=f"{self.POSTGRES_DB}",
        )

    # --- JWT Security Settings ---
    SECRET_KEY: str = "YOUR_SUPER_SECRET_KEY_NEVER_HARDCODE_IN_PROD" # CHANGE THIS!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # Token expires in 24 hours

    # --- Project Metadata ---
    PROJECT_NAME: str = "Uniform Patient Record Platform"
    PROJECT_VERSION: str = "1.0.0"

settings = Settings()