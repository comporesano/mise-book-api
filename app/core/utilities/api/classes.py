from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Кастомный класс для API-респонсов"""

    model_config = ConfigDict(from_attributes=True)

    status: str = "success"
    message: str = "Success"
    data: T | None = None
    status_code: int = 200

    @classmethod
    def ok(
        cls,
        data: T = None,
        message: str = "Success",
        status_code: int = 200,
    ) -> APIResponse[T]:
        """Метод для 1хх 2хх 3хх."""
        return cls(
            status="success" if status_code < 400 else "error",
            message=message,
            data=data,
            status_code=status_code,
        )

    @classmethod
    def error(
        cls,
        message: str = "Error",
        status_code: int = 400,
    ) -> APIResponse[T]:
        """Метод для 4хх и 5хх."""
        return cls(
            status="error",
            message=message,
            data=None,
            status_code=status_code,
        )
