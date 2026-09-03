from fastapi import APIRouter

from app.api import bookings

router = APIRouter(prefix="/api/v1")
router.include_router(bookings.router)
