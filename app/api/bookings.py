from core.utilities.classes import APIResponse
from fastapi import APIRouter, status

router = APIRouter()


@router.get(path="/")
def get_bookings_list() -> APIResponse:
    return APIResponse(content={})


@router.get(path="/{book_id}")
def get_booking_info(book_id: int) -> APIResponse:
    return APIResponse(content={})


@router.post(path="/")
def create_booking() -> APIResponse:
    return APIResponse(content={}, status_code=status.HTTP_201_CREATED)


@router.delete(path="/")
def delete_booking() -> APIResponse:
    return APIResponse(content={})
