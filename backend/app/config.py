from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    app_name: str = "AI Incident Intelligence Platform"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    sqs_queue_url: str = ""
    anthropic_api_key: str = ""
    supabase_db_url: str = ""
    groq_api_key: str = ""
    llm_provider: str = "claude"
    # Comma-separated list, set via CORS_ALLOWED_ORIGINS on Render for the
    # deployed frontend's real origin. Defaults cover local dev only.
    cors_allowed_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

settings = Settings()