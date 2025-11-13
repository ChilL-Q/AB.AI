from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    OPENAI_API_KEY: str | None = None
    TELEGRAM_BOT_TOKEN: str | None = None
    DATABASE_URL: str = "sqlite+aiosqlite:///./abai.db"
    AI_MODEL: str = "gpt-4o-mini"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
