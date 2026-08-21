from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Veyra Finance"
    app_version: str = "1.0.0"
    environment: str = "development"

    database_url: str = "postgresql+psycopg://localhost/veyra"

    openai_api_key: str = ""

    encryption_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
