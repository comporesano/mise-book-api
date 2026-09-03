import logging
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.exceptions import BookingNotFoundError, SlotAlreadyTakenError
from app.core.utilities.api.classes import APIResponse
from app.schemas import GetBooking, PostBookingSchema
from app.services.repository.booking import BookingRepository

router = APIRouter(prefix="/bookings")

SessionDep = Annotated[AsyncSession, Depends(get_async_session)]

logger = logging.getLogger(__name__)


@router.post(
    path="",
    response_model=APIResponse[GetBooking],
    status_code=status.HTTP_201_CREATED,
)
async def create_booking(
    payload: PostBookingSchema,
    session: SessionDep,
) -> APIResponse:
    """
    POST /api/v1/bookings/

    Создать бронь."""
    repo = BookingRepository(session)
    try:
        booking = await repo.create_booking(**payload.model_dump())
    except SlotAlreadyTakenError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return APIResponse.ok(
        data=booking,
        message="Created successfully!",
        status_code=status.HTTP_201_CREATED
    )


@router.get(
    path="",
    response_model=APIResponse[list[GetBooking]],
)
async def get_bookings_list(
    session: SessionDep,
    date: Annotated[
        date | None, Query(description="Фильтр по дате бронирования (YYYY-MM-DD)")
    ] = None,
) -> APIResponse:
    """
    GET /api/v1/bookings/

    Список броней, отфильтрованный(Опционально) по дате.
    """
    repo = BookingRepository(session)
    bookings = await repo.get_all(date)
    return APIResponse.ok(data=[b for b in bookings])


@router.get(
    path="/{book_id}",
    response_model=APIResponse[GetBooking],
)
async def get_booking_info(
    book_id: int,
    session: SessionDep,
) -> APIResponse:
    """
    GET /api/v1/bookings/<id>/

    Бронь по id. 404, если не найдена.
    """
    repo = BookingRepository(session)
    try:
        booking = await repo.get_booking(book_id)
    except BookingNotFoundError as exc:
        logger.warning("Booking not found: id=%s", book_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return APIResponse.ok(data=booking)


@router.delete(
    "/{book_id}",
    response_model=APIResponse[GetBooking],
)
async def delete_booking(
    book_id: int,
    session: SessionDep,
) -> APIResponse:
    """
    DELETE /api/v1/bookings/<id>/

    Отменить бронь: статус меняется на cancelled, запись остаётся.
    """
    repo = BookingRepository(session)
    try:
        booking = await repo.cancel_booking(book_id)
    except BookingNotFoundError as exc:
        logger.warning("Booking not found: id=%s", book_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return APIResponse.ok(data=booking)
