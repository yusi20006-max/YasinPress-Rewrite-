from yasinpress.api.app import ApiApp
from yasinpress.api.auth import TokenAuth
from yasinpress.api.request import Request
from yasinpress.api.responses import ok


def test_request_parses_query_and_bearer_token() -> None:
    request = Request.from_target(
        "/api/articles?page=2&source=bbc&source=irna",
        headers={"Authorization": "Bearer secret"},
    )
    assert request.path == "/api/articles"
    assert request.query_value("page") == "2"
    assert request.query["source"] == ("bbc", "irna")
    assert request.bearer_token == "secret"


def test_router_supports_methods_and_legacy_handlers() -> None:
    app = ApiApp()
    app.route("/health", lambda: ok({"healthy": True}))
    app.route("/health", lambda request: ok({"method": request.method}), method="POST")

    assert app.handle("/health").body == {"healthy": True}
    assert app.handle("/health", method="POST").body == {"method": "POST"}
    assert app.handle("/health", method="PUT").status_code == 405


def test_protected_route_requires_bearer_auth() -> None:
    app = ApiApp(auth=TokenAuth("secret"))
    app.route("/api/retry", lambda: ok({"ok": True}), method="POST", protected=True)

    assert app.handle("/api/retry", method="POST").status_code == 401
    assert app.handle(
        "/api/retry",
        method="POST",
        headers={"Authorization": "Bearer secret"},
    ).status_code == 200
