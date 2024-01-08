import dotenv
from pydantic import BaseModel

from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresqlSettings(BaseModel):
    PORT: int
    PASSWORD: str
    USER: str
    NAME: str
    HOST: str
    HOSTNAME: str


class AuthSettings(BaseModel):
    KEY: str


class Settings(BaseSettings):
    DB: PostgresqlSettings
    AUTH: AuthSettings

    model_config = SettingsConfigDict(
        env_file=dotenv.find_dotenv(".env"),
        env_nested_delimiter="_",
    )


settings = Settings()
