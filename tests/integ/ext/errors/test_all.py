from flaskel.ext.errors.dispatchers import URLPrefixDispatcher


def test_app_runs(client):
    res = client.get("/")
    assert res.status_code == 404
    assert res.get_json()["type"] == "https://httpstatuses.com/404"


def test_method_not_allowed(client):
    res = client.post("/api")
    assert res.status_code == 405
    assert "Allow" in res.headers
    assert "allowed" in res.get_json()["response"]
    assert res.get_json()["type"] == "https://httpstatuses.com/405"


def test_api(client):
    res = client.get("/api")
    assert res.status_code == 500
    assert res.headers.get("Content-Type") == "application/problem+json"

    data = res.get_json()
    assert data["type"] == "https://httpstatuses.com/500"
    assert data["title"] == "Internal Server Error"
    assert data["detail"] is not None
    assert data["status"] == 500
    assert data["instance"] == "about:blank"
    assert data["response"] is None


def test_api_error(client):
    res = client.get("/api/error")
    assert res.status_code == 500
    assert res.headers.get("Content-Type") == "application/problem+json"


def test_web(client):
    res = client.get("/web/web")
    assert res.status_code == 500
    assert res.headers.get("Content-Type") == "text/html; charset=utf-8"


def test_web_redirect(client):
    res = client.get("/web/redirect")
    assert res.status_code == 308
    assert res.headers.get("Content-Type") == "text/html; charset=utf-8"
    assert res.headers.get("Location").endswith("/web")


def test_web_xhr(client):
    res = client.get("/web/web", headers={"X-Requested-With": "XMLHttpRequest"})
    assert res.status_code == 500
    assert res.headers.get("Content-Type") == "application/problem+json"


def test_web_error(client):
    res = client.get("/web/web/error")
    assert res.status_code == 500
    assert res.headers.get("Content-Type") == "text/html; charset=utf-8"


def method_not_allowed(client):
    res = client.get("/methodnotallowed")
    assert res.status_code == 405
    assert res.headers.get("Allow") is None

    res = client.get("/methodnotallowed/options")
    assert res.status_code == 405
    assert res.headers["Allow"] == "GET, POST"
    assert res.get_json()["response"]["Allow"] == ["GET", "POST"]


def test_custom(client, app):
    res = client.get(
        "/custom/custom", base_url="http://api." + app.config["SERVER_NAME"]
    )
    assert res.status_code == 404
    assert res.headers.get("Content-Type") == "text/html"


def test_dispatch_error_web(client, app, error_handler):
    error_handler.register_dispatcher(app, URLPrefixDispatcher)
    res = client.get("/web/web/page-not-found")
    assert res.status_code == 404
    assert "text/html" in res.headers["Content-Type"]


def test_dispatch_error_api(client, app):
    res = client.get(
        "/api-not-found", base_url="http://api." + app.config["SERVER_NAME"]
    )
    assert res.status_code == 404
    assert "text/html" in res.headers["Content-Type"]
    assert "test" in res.headers["custom"]


def test_dispatch_default(client, app, error_handler):
    error_handler.register_dispatcher(app, dispatcher="default")
    res = client.get("/not-found")
    assert res.status_code == 404
    assert "text/html" in res.headers["Content-Type"]
    assert "https://httpstatuses.com/404" in res.data.decode()

    res = client.post("/not-allowed")
    assert res.status_code == 405
    assert "text/html" in res.headers["Content-Type"]
    assert "https://httpstatuses.com/405" in res.data.decode()


def test_permanent_redirect(client):
    res = client.get("/permanent")
    assert res.status_code in (301, 308)
    assert "Location" in res.headers


def test_response(client):
    res = client.get("/api/response")
    assert res.status_code == 500
    assert res.data == b"response"


def test_unauthorized(client):
    res = client.get("/api/unauthorized")
    assert res.status_code == 401
    assert res.headers["WWW-Authenticate"] == 'Basic realm="authentication required"'
    auth = res.get_json()["response"]["authenticate"][0]
    assert auth["auth_type"] == "basic"
    assert auth["realm"] == "authentication required"


def test_retry_after(client):
    date = "Wed, 01 Mar 2000 00:00:00 GMT"
    res = client.get("/api/retry")
    assert res.status_code == 429
    assert res.headers["Retry-After"] == date
    assert res.get_json()["response"]["retry_after"] == date


def test_range(client):
    res = client.get("/api/range")
    assert res.status_code == 416
    assert res.headers["Content-Range"] == "bytes */10"
    data = res.get_json()["response"]
    assert data["length"] == 10
    assert data["units"] == "bytes"
