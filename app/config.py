from pydantic import BaseSettings, SecretStr


class Settings(BaseSettings):
    secret_key: SecretStr

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings()
