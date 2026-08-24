from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./weathergpt.db"
    cors_origins: str = "http://localhost:5173"
    request_timeout_seconds: float = 8.0
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
