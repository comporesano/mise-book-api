from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Базовый конфиг всего приложения."""

    app_name: str = "Booking API for MISE"
    debug: bool = False

    # База данных: значения читаются из переменных окружения DB_* / .env
    db_user: str = "booking"
    db_passwd: str = "booking"
    db_name: str = "bookings"
    db_host: str = "localhost"
    db_port: int = 5432

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_passwd}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
