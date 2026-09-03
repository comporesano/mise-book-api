import json
from typing import Any

from fastapi.responses import Response


class APIResponse(Response):
    media_type = "application/json"

    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        message: str = "Success",
        **kwargs
    ):
        body = {
            "status": "success" if status_code < 400 else "error",
            "message": message,
            "data": content,
            "status_code": status_code
        }
        super().__init__(
            content=json.dumps(body),
            status_code=status_code,
            **kwargs
        )
