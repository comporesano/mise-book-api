from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения. Читаются из переменных окружения и .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Booking API for MISE"
    debug: bool = False

    # PostgreSQL
    postgres_user: str = "booking"
    postgres_password: str = "booking"
    postgres_db: str = "bookings"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    database_url: str = "postgresql+asyncpg://booking:booking@localhost:5432/bookings"


settings = Settings()
