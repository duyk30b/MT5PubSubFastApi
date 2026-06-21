from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseSettings):
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    REDIS_PROTOCOL: int = 2

    model_config = SettingsConfigDict(env_file_encoding="utf-8", extra="ignore")


redis_settings = RedisSettings()
