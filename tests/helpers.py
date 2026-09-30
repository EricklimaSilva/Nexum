from __future__ import annotations

from flask import Response


def assert_redirect_to_login(response: Response, *, path: str = "/auth/login") -> None:
    assert response.status_code in {301, 302, 303}
    assert path in response.headers.get("Location", "")
