from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    app_name: str = "AI Incident Intelligence Platform"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    sqs_queue_url: str = ""
    anthropic_api_key: str = ""

    class Config:
        env_file = ".env"

settings = Settings()