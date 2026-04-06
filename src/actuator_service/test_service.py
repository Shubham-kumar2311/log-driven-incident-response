"""
Actuator Service - Test Script

Tests all actions and endpoints.
"""
import asyncio
import httpx
import sys
import os

BASE_URL = os.getenv("ACTUATOR_TEST_URL", "http://localhost:8007")


async def test_health():
    """Test health endpoint."""
    print("\n" + "=" * 60)
    print("TEST: Health Check")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        data = response.json()

        print(f"Status: {response.status_code}")
        print(f"Service Status: {data.get('status')}")
        print(f"Actions Registered: {data.get('action_count')}")
        print(f"Redis Mode: {data.get('use_redis')}")

        assert response.status_code == 200
        assert data["status"] == "healthy"
        print("PASSED")


async def test_actions_list():
    """Test actions list endpoint."""
    print("\n" + "=" * 60)
    print("TEST: Get Actions List")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/actions")
        data = response.json()

        print(f"Actions Count: {data.get('count')}")
        print(f"Actions: {', '.join(data.get('actions', []))}")

        assert response.status_code == 200
        assert data["count"] > 0
        print("PASSED")


async def test_execute_restart_database():
    """Test restart_database action."""
    print("\n" + "=" * 60)
    print("TEST: Execute restart_database")
    print("=" * 60)

    payload = {
        "incident_id": "INC-001",
        "action": "restart_database",
        "parameters": {"container": "postgres-db"}
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/execute", json=payload)
        data = response.json()

        print(f"Status: {response.status_code}")
        print(f"Incident ID: {data.get('incident_id')}")
        print(f"Action: {data.get('action')}")
        print(f"Execution Status: {data.get('execution_status')}")
        print(f"Output: {data.get('output')}")
        print(f"Duration: {data.get('duration_ms')}ms")
        print(f"Mode: {data.get('mode')}")

        assert response.status_code == 200
        assert data["execution_status"] == "success"
        print("PASSED")


async def test_execute_restart_api():
    """Test restart_api action."""
    print("\n" + "=" * 60)
    print("TEST: Execute restart_api")
    print("=" * 60)

    payload = {
        "incident_id": "INC-002",
        "action": "restart_api"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/execute", json=payload)
        data = response.json()

        print(f"Execution Status: {data.get('execution_status')}")
        print(f"Output: {data.get('output')}")
        print(f"Mode: {data.get('mode')}")

        assert response.status_code == 200
        assert data["execution_status"] == "success"
        print("PASSED")


async def test_execute_lock_accounts():
    """Test lock_accounts action."""
    print("\n" + "=" * 60)
    print("TEST: Execute lock_accounts")
    print("=" * 60)

    payload = {
        "incident_id": "INC-003",
        "action": "lock_accounts",
        "parameters": {
            "source_ip": "192.168.1.100",
            "lock_duration_minutes": 60
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/execute", json=payload)
        data = response.json()

        print(f"Execution Status: {data.get('execution_status')}")
        print(f"Output: {data.get('output')}")
        print(f"Details: {data.get('details')}")

        assert response.status_code == 200
        assert data["execution_status"] == "success"
        print("PASSED")


async def test_execute_rollback_deployment():
    """Test rollback_deployment action."""
    print("\n" + "=" * 60)
    print("TEST: Execute rollback_deployment")
    print("=" * 60)

    payload = {
        "incident_id": "INC-004",
        "action": "rollback_deployment",
        "parameters": {
            "deployment_id": "deploy-abc123",
            "target_version": "v1.2.3"
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/execute", json=payload)
        data = response.json()

        print(f"Execution Status: {data.get('execution_status')}")
        print(f"Output: {data.get('output')}")

        assert response.status_code == 200
        assert data["execution_status"] == "success"
        print("PASSED")


async def test_execute_unknown_action():
    """Test unknown action (should return no_handler)."""
    print("\n" + "=" * 60)
    print("TEST: Execute unknown action")
    print("=" * 60)

    payload = {
        "incident_id": "INC-005",
        "action": "unknown_action"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/execute", json=payload)
        data = response.json()

        print(f"Execution Status: {data.get('execution_status')}")
        print(f"Output: {data.get('output')}")

        assert response.status_code == 200
        assert data["execution_status"] == "no_handler"
        print("PASSED")


async def test_batch_execute():
    """Test batch execution."""
    print("\n" + "=" * 60)
    print("TEST: Batch Execute")
    print("=" * 60)

    payload = {
        "actions": [
            {"incident_id": "INC-006", "action": "restart_cache"},
            {"incident_id": "INC-006", "action": "clear_cache"},
            {"incident_id": "INC-006", "action": "notify_oncall"}
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/execute/batch", json=payload)
        data = response.json()

        print(f"Results Count: {len(data)}")
        for i, result in enumerate(data):
            print(f"  [{i+1}] {result['action']}: {result['execution_status']}")

        assert response.status_code == 200
        assert len(data) == 3
        assert all(r["execution_status"] == "success" for r in data)
        print("PASSED")


async def test_history():
    """Test execution history endpoint."""
    print("\n" + "=" * 60)
    print("TEST: Execution History")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/history?limit=10")
        data = response.json()

        print(f"Executions in history: {data.get('count')}")

        assert response.status_code == 200
        assert data["count"] > 0
        print("PASSED")


async def test_metrics():
    """Test metrics endpoint."""
    print("\n" + "=" * 60)
    print("TEST: Metrics")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/metrics")
        data = response.json()

        print(f"Total Executions: {data.get('total_executions')}")
        print(f"Success Count: {data.get('success_count')}")
        print(f"Failed Count: {data.get('failed_count')}")
        print(f"Success Rate: {data.get('success_rate_percent')}%")

        assert response.status_code == 200
        print("PASSED")


async def test_dashboard():
    """Test dashboard endpoint."""
    print("\n" + "=" * 60)
    print("TEST: Dashboard")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/")

        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"HTML Length: {len(response.text)} chars")

        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        print("PASSED")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ACTUATOR SERVICE TEST SUITE")
    print("=" * 60)
    print(f"Target: {BASE_URL}")

    try:
        await test_health()
        await test_actions_list()
        await test_execute_restart_database()
        await test_execute_restart_api()
        await test_execute_lock_accounts()
        await test_execute_rollback_deployment()
        await test_execute_unknown_action()
        await test_batch_execute()
        await test_history()
        await test_metrics()
        await test_dashboard()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)

    except httpx.ConnectError:
        print("\nERROR: Cannot connect to service.")
        print(f"Make sure the service is running at {BASE_URL}")
        print("\nTo start the service:")
        print("  cd src/actuator_service")
        print("  pip install -r requirements.txt")
        print("  python app.py")
        sys.exit(1)

    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
