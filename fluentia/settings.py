from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_PORT: int

    def database_url(self, database_name) -> str:
        return str(
            PostgresDsn.build(
                scheme='postgresql',
                username=self.DATABASE_USER,
                password=self.DATABASE_PASSWORD,
                host=self.DATABASE_HOST,
                port=self.DATABASE_PORT,
                path=database_name,
            )
        )
