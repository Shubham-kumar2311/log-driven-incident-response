from pathlib import Path
import importlib.util
import sys
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.requests import Request


AUTH_SERVICE_DIR = Path(__file__).resolve().parents[1]
if str(AUTH_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AUTH_SERVICE_DIR))


def _load_module(module_name: str, module_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


password_utils = _load_module("auth_password_utils", AUTH_SERVICE_DIR / "utils" / "password.py")
jwt_utils = _load_module("auth_jwt_utils", AUTH_SERVICE_DIR / "utils" / "jwt.py")
auth_routes = _load_module("auth_routes_module", AUTH_SERVICE_DIR / "auth" / "routes.py")


@pytest.mark.parametrize(
    "password,expected_reason",
    [
        pytest.param("short1!", "at least 8 characters", id="too-short"),
        pytest.param("alllowercase1!", "uppercase letter", id="no-uppercase"),
        pytest.param("ALLUPPERCASE1!", "lowercase letter", id="no-lowercase"),
        pytest.param("NoDigits!", "one digit", id="no-digit"),
        pytest.param("NoSpecial123", "one special character", id="no-special"),
    ],
)
def test_validate_password_strength_rejects_weak_passwords(password, expected_reason):
    is_valid, msg = password_utils.validate_password_strength(password)
    assert is_valid is False
    assert expected_reason in msg


def test_validate_password_strength_accepts_valid_password():
    is_valid, msg = password_utils.validate_password_strength("Str0ng!Pass")
    assert is_valid is True
    assert msg == ""


def test_create_and_verify_token_roundtrip():
    token = jwt_utils.create_token(user_id="user-1", role="ADMIN")
    payload = jwt_utils.verify_token(token)

    assert payload is not None
    assert payload["user_id"] == "user-1"
    assert payload["role"] == "ADMIN"
    assert payload["iss"] == "auth-server"


def test_verify_token_returns_none_for_invalid_token():
    assert jwt_utils.verify_token("not-a-valid-token") is None


def test_get_client_ip_prefers_x_forwarded_for():
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [(b"x-forwarded-for", b"203.0.113.42, 10.0.0.2")],
            "client": ("127.0.0.1", 5000),
            "query_string": b"",
        }
    )

    assert auth_routes.get_client_ip(request) == "203.0.113.42"


def test_set_and_delete_auth_cookie_headers_present():
    response = JSONResponse(content={"ok": True})
    auth_routes.set_auth_cookie(response, token="abc.def.ghi")

    set_cookie_header = response.headers.get("set-cookie", "")
    assert auth_routes.settings.COOKIE_NAME in set_cookie_header
    assert "httponly" in set_cookie_header.lower()

    delete_response = JSONResponse(content={"ok": True})
    auth_routes.delete_auth_cookie(delete_response)
    delete_cookie_header = delete_response.headers.get("set-cookie", "")
    assert auth_routes.settings.COOKIE_NAME in delete_cookie_header


@pytest.mark.anyio
async def test_require_admin_user_returns_admin(monkeypatch):
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/admin/users",
            "headers": [],
            "client": ("127.0.0.1", 5000),
            "query_string": b"",
        }
    )

    admin = {"id": "u1", "username": "root", "role": "ADMIN", "is_active": True}
    monkeypatch.setattr(auth_routes, "get_authenticated_user", AsyncMock(return_value=admin))

    result = await auth_routes.require_admin_user(request)
    assert result["role"] == "ADMIN"


@pytest.mark.anyio
async def test_require_admin_user_raises_401_when_not_authenticated(monkeypatch):
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/admin/users",
            "headers": [],
            "client": ("127.0.0.1", 5000),
            "query_string": b"",
        }
    )

    monkeypatch.setattr(auth_routes, "get_authenticated_user", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_info:
        await auth_routes.require_admin_user(request)

    assert exc_info.value.status_code == 401


@pytest.mark.anyio
async def test_require_admin_user_raises_403_for_non_admin(monkeypatch):
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/admin/users",
            "headers": [],
            "client": ("127.0.0.1", 5000),
            "query_string": b"",
        }
    )

    analyst = {"id": "u2", "username": "analyst", "role": "ANALYST", "is_active": True}
    monkeypatch.setattr(auth_routes, "get_authenticated_user", AsyncMock(return_value=analyst))

    with pytest.raises(HTTPException) as exc_info:
        await auth_routes.require_admin_user(request)

    assert exc_info.value.status_code == 403
