import logging

from app.core.config import settings


def configure_logging() -> None:
    """Конфиг логирования. Управлять через DEBUG в .env"""
    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    logging.getLogger("app").setLevel(logging.DEBUG if settings.debug else logging.INFO)
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_logger.setLevel(logging.WARNING)
    sqlalchemy_logger.propagate = False
