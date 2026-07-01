from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    app_name: str = "AI Incident Intelligence Platform"

    class Config:
        env_file = ".env"

settings = Settings()