import os
from pathlib import Path
import sys
from uuid import uuid4

import pytest


AUTH_SERVICE_DIR = Path(__file__).resolve().parents[1]
if str(AUTH_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AUTH_SERVICE_DIR))

from database import Database
from models import LoginLog, LoginStatus, User, UserRole


AUTH_DB_INTEGRATION = os.getenv("AUTH_DB_INTEGRATION", "1") == "1"

pytestmark = pytest.mark.skipif(
    not AUTH_DB_INTEGRATION,
    reason="Integration tests are disabled. Turn on with AUTH_DB_INTEGRATION=1",
)


@pytest.fixture(scope="module", autouse=True)
async def db_connection():
    try:
        await Database.connect()
    except Exception as exc:
        pytest.skip(f"MongoDB not available for integration tests: {exc}")

    yield

    await Database.disconnect()


@pytest.mark.anyio
async def test_user_create_persists_in_db():
    suffix = uuid4().hex[:8]
    username = f"it_user_{suffix}"
    email = f"it_{suffix}@example.com"

    user = await User.create(
        username=username,
        email=email,
        password="Str0ng!Pass",
        role=UserRole.USER,
    )

    assert user["id"]
    assert user["username"] == username
    assert user["email"] == email
    assert user["role"] == UserRole.USER.value

    fetched = await User.find_by_username(username)
    assert fetched is not None
    assert fetched["id"] == user["id"]


@pytest.mark.anyio
async def test_login_log_create_persists_in_db():
    suffix = uuid4().hex[:8]
    attempted_username = f"it_login_{suffix}"

    log = await LoginLog.create(
        user_id=None,
        username_attempted=attempted_username,
        ip_address="203.0.113.42",
        status=LoginStatus.FAILED,
        user_agent="pytest-integration",
        failure_reason="integration-test",
    )

    assert log["id"]
    assert log["status"] == LoginStatus.FAILED.value
    assert log["username_attempted"] == attempted_username

    failed_count = await LoginLog.get_recent_failed_by_ip("203.0.113.42", window_seconds=300)
    assert failed_count >= 1
