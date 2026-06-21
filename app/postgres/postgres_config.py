from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DATABASE_NAME: str = "postgres_database"
    POSTGRES_USER: str = "postgres_user"
    POSTGRES_PASSWORD: str = "postgres_password"
    POSTGRES_URI_MIGRATION: str = ""
    POSTGRES_URI_APP: str = ""
    model_config = SettingsConfigDict(env_file_encoding="utf-8", extra="ignore")

    @property
    def sqlalchemy_uri_migration(self) -> str:
        if self.POSTGRES_URI_MIGRATION:
            return f"postgresql+psycopg2://{self.POSTGRES_URI_MIGRATION}"
        else:
            return (
                f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DATABASE_NAME}"
            )

    @property
    def sqlalchemy_uri_app(self) -> str:
        if self.POSTGRES_URI_APP:
            return f"postgresql+asyncpg://{self.POSTGRES_URI_APP}"
        else:
            return (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DATABASE_NAME}"
            )


postgres_settings = PostgresSettings()
