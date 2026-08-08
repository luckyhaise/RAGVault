
from pydantic_settings import BaseSettings ,SettingsConfigDict
from pydantic import PostgresDsn
from os import getenv

ENV_FILE = getenv("ENV_FILE",".env")

class Settings(BaseSettings):
    postgres_url:PostgresDsn
    access_token_expire_minutes: int
    jwt_secret_key: str
    jwt_algorithm: str
    regex:str = r"^[a-zA-Z0-9@#_!$%*.\-]+$" 
    resend_api_key : str
    verification_email:str
    model_config = SettingsConfigDict(env_file=ENV_FILE,env_file_encoding="utf-8",extra="allow")

settings = Settings()

