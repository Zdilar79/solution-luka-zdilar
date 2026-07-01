from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "TicketHub"
    debug: bool = False

    database_url: str = (
        "postgresql+asyncpg://tickethub:tickethub@localhost:5432/tickethub"
    )

    dummyjson_base_url: str = "https://dummyjson.com"
    http_timeout: float = 10.0

    sync_on_startup: bool = True
    background_sync_interval_seconds: int = 0

    default_page_size: int = 20
    max_page_size: int = 100


settings = Settings()