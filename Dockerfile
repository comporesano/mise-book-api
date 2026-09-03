FROM python:3.12-slim

# uv из официального образа (версия совпадает с локальной)
COPY --from=ghcr.io/astral-sh/uv:0.6.13 /uv /uvx /bin/

WORKDIR /app

# Сначала зависимости - слой кешируется, пока не меняются pyproject.toml/uv.lock
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Код приложения и миграции
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Применяем миграции и запускаем API
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
