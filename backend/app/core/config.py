from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_env: str = "development"
    secret_key: str = "change-me-in-production"
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8081"]

    # Database
    database_url: str = "postgresql+asyncpg://abai:abai@localhost:5432/abai"
    database_sync_url: str = "postgresql://abai:abai@localhost:5432/abai"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # JWT
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # WhatsApp
    whatsapp_phone_number_id: str = ""
    whatsapp_access_token: str = ""
    whatsapp_verify_token: str = ""
    # Shared secret for self-hosted inbound webhooks (bridges, tests).
    inbound_webhook_secret: str = ""

    # Telegram
    telegram_bot_token: str = ""

    # Claude / Anthropic
    anthropic_api_key: str = ""

    # Email
    resend_api_key: str = ""
    email_from: str = "noreply@ab-ai.app"

    # Storage
    s3_endpoint: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket: str = "ab-ai"

    # Billing
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    kaspi_merchant_id: str = ""
    kaspi_api_key: str = ""

    # Monitoring
    sentry_dsn: str = ""
    posthog_api_key: str = ""

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()
