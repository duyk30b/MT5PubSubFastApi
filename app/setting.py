from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FastAPI Demo"
    env: str = "dev"
    api_port: int = 8000

    jwt_access_key: str = "default_access_secret_key"
    jwt_refresh_key: str = "default_refresh_secret_key"
    jwt_access_seconds: int = 3600  # 1 hour
    jwt_refresh_seconds: int = 2592000  # 30 days
    jwt_algorithm: str = "HS256"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings: Settings = Settings()
