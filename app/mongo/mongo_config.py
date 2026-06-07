from alembic.op import f
from pydantic_settings import BaseSettings, SettingsConfigDict


class MongoSettings(BaseSettings):
    MONGO_HOST: str = "localhost"
    MONGO_PORT: int = 27017
    MONGO_DATABASE_NAME: str = "mongo_database"
    MONGO_USERNAME: str = "mongo_user"
    MONGO_PASSWORD: str = "mongo_password"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def mongo_uri(self) -> str:
        return (
            f"mongodb://{self.MONGO_USERNAME}:{self.MONGO_PASSWORD}"
            f"@{self.MONGO_HOST}:{self.MONGO_PORT}/{self.MONGO_DATABASE_NAME}"
            f"?authSource=admin"
        )


mongo_settings = MongoSettings()
