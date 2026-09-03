import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import core
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(title=settings.app_name)
app.include_router(core.router)

logger = logging.getLogger(__name__)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Непредвиденные ошибки: логируем с traceback, наружу отдаём 500 без деталей."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
