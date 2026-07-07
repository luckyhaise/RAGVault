from pydantic_settings import BaseSettings ,SettingsConfigDict
from pydantic import PostgresDsn

class Settings(BaseSettings):
    postgres_url:PostgresDsn
    resend_api_key : str
    verification_email:str
    model_config = SettingsConfigDict(env_file=".env",env_file_encoding="utf-8",extra="ignore")

settings = Settings()
