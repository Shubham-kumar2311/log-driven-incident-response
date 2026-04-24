from pathlib import Path
import importlib.util
import importlib
import sys
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
import pytest


AUTH_SERVICE_DIR = Path(__file__).resolve().parents[1]
if str(AUTH_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AUTH_SERVICE_DIR))


def _load_module(module_name: str, module_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


auth_app = _load_module("auth_service_app", AUTH_SERVICE_DIR / "app.py")
auth_routes = importlib.import_module("auth.routes")
auth_db = importlib.import_module("database")


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(auth_db.Database, "connect", AsyncMock(return_value=None))
    monkeypatch.setattr(auth_db.Database, "disconnect", AsyncMock(return_value=None))

    with TestClient(auth_app.app) as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "auth_server"


def test_register_success(client, monkeypatch):
    user_result = {
        "id": "u100",
        "username": "newuser",
        "email": "new@example.com",
        "role": "USER",
    }

    monkeypatch.setattr(auth_routes, "validate_password_strength", lambda p: (True, ""))
    monkeypatch.setattr(auth_routes.User, "exists_by_username", AsyncMock(return_value=False))
    monkeypatch.setattr(auth_routes.User, "exists_by_email", AsyncMock(return_value=False))
    monkeypatch.setattr(auth_routes.User, "create", AsyncMock(return_value=user_result))
    monkeypatch.setattr(auth_routes, "send_registration_event", AsyncMock(return_value=None))

    response = client.post(
        "/register",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "Str0ng!Pass",
            "role": "ADMIN",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["user"]["role"] == "USER"


def test_login_invalid_credentials(client, monkeypatch):
    monkeypatch.setattr(auth_routes.User, "find_by_username_or_email", AsyncMock(return_value=None))
    monkeypatch.setattr(auth_routes.LoginLog, "create", AsyncMock(return_value={"id": "l1"}))
    monkeypatch.setattr(auth_routes.LoginLog, "get_recent_failed_by_ip", AsyncMock(return_value=2))
    monkeypatch.setattr(auth_routes, "send_login_event", AsyncMock(return_value=None))

    response = client.post(
        "/login",
        json={"username": "unknown", "password": "Wrong!123"},
        headers={"User-Agent": "pytest", "X-Forwarded-For": "203.0.113.10"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_login_success_sets_cookie_and_redirect(client, monkeypatch):
    user = {
        "id": "u200",
        "username": "admin",
        "email": "admin@example.com",
        "role": "ADMIN",
        "is_active": True,
        "password_hash": "hashed",
    }

    monkeypatch.setattr(auth_routes.User, "find_by_username_or_email", AsyncMock(return_value=user))
    monkeypatch.setattr(auth_routes, "verify_password", lambda plain, hashed: True)
    monkeypatch.setattr(auth_routes.LoginLog, "is_new_ip_for_user", AsyncMock(return_value=False))
    monkeypatch.setattr(auth_routes.LoginLog, "create", AsyncMock(return_value={"id": "l2"}))
    monkeypatch.setattr(auth_routes.User, "update_last_login", AsyncMock(return_value=None))
    monkeypatch.setattr(auth_routes, "send_login_event", AsyncMock(return_value=None))
    monkeypatch.setattr(auth_routes, "create_token", lambda user_id, role: "jwt.token.value")

    response = client.post(
        "/login",
        json={"username": "admin", "password": "Admin!123"},
        headers={"User-Agent": "pytest", "X-Forwarded-For": "203.0.113.11"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["redirect_url"] == auth_routes.settings.ROLE_REDIRECTS["ADMIN"]
    assert auth_routes.settings.COOKIE_NAME in response.headers.get("set-cookie", "")


def test_verify_requires_cookie(client):
    response = client.get("/verify")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_verify_success_with_valid_token(client, monkeypatch):
    monkeypatch.setattr(auth_routes, "verify_token", lambda token: {"user_id": "u300"})
    monkeypatch.setattr(
        auth_routes.User,
        "find_by_id",
        AsyncMock(
            return_value={
                "id": "u300",
                "username": "analyst",
                "email": "analyst@example.com",
                "role": "ANALYST",
                "is_active": True,
            }
        ),
    )

    client.cookies.set(auth_routes.settings.COOKIE_NAME, "valid.token")
    response = client.get("/verify")

    assert response.status_code == 200
    body = response.json()
    assert body["authenticated"] is True
    assert body["user"]["role"] == "ANALYST"


def test_logout_clears_cookie(client):
    response = client.post("/logout")

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert auth_routes.settings.COOKIE_NAME in response.headers.get("set-cookie", "")
