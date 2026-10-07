from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "HostelHub API"
    database_url: str = "postgresql+psycopg://hostelhub:hostelhub@localhost:5432/hostelhub"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
