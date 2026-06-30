from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    environment: str = "development"
    secret_key: str = "dev-secret-change-in-production"
    cors_origins: str = "http://localhost:3000"

    # Database (Supabase PostgreSQL)
    database_url: str = "postgresql://postgres:password@localhost:5432/tfaiqc"

    # Cloudflare R2
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = "tf-ai-qc-reports"

    # Ollama
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "glm-4.7-flash"

    # Claude API (fallback if Ollama unreachable)
    anthropic_api_key: str = ""

    # Bubble
    bubble_app_name: str = ""
    bubble_api_token: str = ""
    bubble_auth_secret: str = ""  # secret used to verify Bubble tokens
    bubble_data_api_url: str = ""  # Bubble Data API base URL for OMS sync
    bubble_data_api_key: str = ""  # Bubble Data API key

    # Internal cron
    internal_cron_secret: str = ""  # shared secret for Railway cron jobs

    # Resend (email)
    resend_api_key: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def r2_endpoint_url(self) -> str:
        return f"https://{self.r2_account_id}.r2.cloudflarestorage.com"


settings = Settings()
