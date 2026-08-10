from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class HTTPResponse:
    status_code: int
    body: str

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300


class HTTPTransport:
    """Small HTTP boundary used by delivery adapters; domain code never owns HTTP clients."""

    def __init__(self, *, timeout: float = 30.0, client: httpx.Client | None = None) -> None:
        self._owned = client is None
        self.client = client or httpx.Client(timeout=timeout)

    def post_json(self, url: str, payload: dict[str, Any], *, headers: dict[str, str] | None = None) -> HTTPResponse:
        response = self.client.post(url, json=payload, headers=headers)
        return HTTPResponse(response.status_code, response.text)

    def post_text(self, url: str, content: str, *, headers: dict[str, str] | None = None) -> HTTPResponse:
        response = self.client.post(url, content=content, headers=headers)
        return HTTPResponse(response.status_code, response.text)

    def close(self) -> None:
        if self._owned:
            self.client.close()

    def __enter__(self) -> "HTTPTransport":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()
