from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Line Messaging API
    line_channel_secret: str = ""
    line_channel_access_token: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
