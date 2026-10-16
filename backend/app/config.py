"""App settings, read from environment variables (or backend/.env when running by hand)."""

from pydantic_settings import BaseSettings, SettingsConfigDict

LOCAL_POSTGRES = "postgresql+psycopg://hostelhub:hostelhub@localhost:5432/hostelhub"


class HostelSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "HostelHub API"
    # Compose, Helm and the tests all override this with DATABASE_URL.
    database_url: str = LOCAL_POSTGRES


settings = HostelSettings()
