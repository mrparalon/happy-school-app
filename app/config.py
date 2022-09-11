from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).parent / ".env"


class Settings(BaseSettings):
    secret_key: SecretStr
    SERVER_PORT: int = 8000

    API_ID: int
    API_HASH: str
    BOT_TOKEN: str

    EDGEDB_AUTH_BASE_URL: str = "http://localhost:10700/db/edgedb/ext/auth"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding="utf-8"
    )


settings = Settings()  # pyright: ignore [reportGeneralTypeIssues]
