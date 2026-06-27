from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    CAMERA_IP: str
    FASTAPI_URL: str
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
