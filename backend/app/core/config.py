
from os import getenv

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = getenv("ENV_FILE",".env")

class Settings(BaseSettings):
    postgres_url:PostgresDsn
    access_token_expire_minutes: int
    jwt_secret_key: str
    jwt_algorithm: str
    log_in_attempts:int
    create_account_attempts:int
    log_in_block_window_sec: int 
    create_account_block_window_sec:int 
    regex:str = r"^[a-zA-Z0-9@#_!$%*.\-]+$" 
    brevo_api_key : str
    verification_email:str
    refresh_token_expire_days:int
    otp_expire_minutes : int
    redis_url : str
    model_config = SettingsConfigDict(env_file=ENV_FILE,env_file_encoding="utf-8",extra="allow")

settings = Settings() #pyright: ignore
