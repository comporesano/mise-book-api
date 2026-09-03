from datetime import date, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.repository.booking import BookingRepository

API = "/api/v1/bookings"


def make_payload(**overrides) -> dict:
    payload = {
        "name": "Иван Петров",
        "phone": "+79991234567",
        "booking_date": (date.today() + timedelta(days=5)).isoformat(),
        "booking_time": "19:00",
        "guests": 4,
    }
    payload.update(overrides)
    return payload


async def test_create_booking_201(client):
    resp = await client.post(API, json=make_payload())
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "success"
    assert body["status_code"] == 201
    assert body["data"]["id"] == 1
    assert body["data"]["status"] == "active"


async def test_create_booking_normalizes_phone(client):
    resp = await client.post(API, json=make_payload(phone="8 999 123-45-67"))
    assert resp.status_code == 201
    assert resp.json()["data"]["phone"] == "+79991234567"


@pytest.mark.parametrize(
    "bad",
    [
        {"name": "И"},  # короче 2 символов
        {"name": "Иван2"},  # цифры в имени
        {"phone": "12345"},  # не телефон
        {"phone": "+7999123456"},  # не хватает цифр
        {"booking_date": "2020-01-01"},  # прошлое
        {"booking_date": (date.today() + timedelta(days=91)).isoformat()},  # дальше +90
        {"booking_time": "19:30"},  # не почасовой слот
        {"booking_time": "11:00"},  # вне диапазона слотов
        {"guests": 0},  # меньше минимума
        {"guests": 13},  # больше максимума
    ],
)
async def test_create_booking_validation_422(client, bad):
    resp = await client.post(API, json=make_payload(**bad))
    assert resp.status_code == 422


async def test_create_booking_conflict_409(client):
    assert (await client.post(API, json=make_payload())).status_code == 201
    resp = await client.post(API, json=make_payload(name="Пётр Иванов"))
    assert resp.status_code == 409
    assert resp.json()["detail"]


async def test_cancelled_slot_becomes_free(client):
    payload = make_payload()
    booking_id = (await client.post(API, json=payload)).json()["data"]["id"]
    await client.delete(f"{API}/{booking_id}")
    resp = await client.post(API, json=payload)
    assert resp.status_code == 201


async def test_get_bookings_list_and_date_filter(client):
    await client.post(API, json=make_payload())
    await client.post(API, json=make_payload(booking_date=(date.today() + timedelta(days=6)).isoformat()))

    resp = await client.get(API)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2

    resp = await client.get(API, params={"date": (date.today() + timedelta(days=5)).isoformat()})
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1


async def test_get_booking_by_id(client):
    booking_id = (await client.post(API, json=make_payload())).json()["data"]["id"]
    resp = await client.get(f"{API}/{booking_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == booking_id


async def test_get_booking_not_found_404(client):
    resp = await client.get(f"{API}/999")
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Booking not found"}


async def test_cancel_booking(client):
    booking_id = (await client.post(API, json=make_payload())).json()["data"]["id"]
    resp = await client.delete(f"{API}/{booking_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "cancelled"


async def test_cancel_missing_booking_404(client):
    resp = await client.delete(f"{API}/999")
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Booking not found"}


async def test_booking_still_listed_after_cancel(client):
    booking_id = (await client.post(API, json=make_payload())).json()["data"]["id"]
    await client.delete(f"{API}/{booking_id}")
    resp = await client.get(API)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1
    assert resp.json()["data"][0]["status"] == "cancelled"


async def test_unhandled_error_returns_500(monkeypatch):
    """Непредвиденные ошибки глушатся: 500 + {"detail": ...} без traceback наружу.

    Starlette рейзит исключение повторно даже после отправки 500-ответа
    (чтобы сервер мог его залогировать), поэтому для этого теста нужен
    транспорт с raise_app_exceptions=False - иначе httpx кинет ошибку в тест.
    """

    async def boom(self, *args, **kwargs):
        raise RuntimeError("db exploded")

    monkeypatch.setattr(BookingRepository, "get_all", boom)

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(API)
        assert resp.status_code == 500
        assert resp.json() == {"detail": "Internal server error"}
