"""
Shared pytest configuration and fixtures for black box testing
"""
import pytest
import requests
import json
from typing import Dict, Any
import os


@pytest.fixture
def api_base_urls():
    """Fixture providing base URLs for all microservices"""
    return {
        "auth": os.getenv("AUTH_SERVICE_URL", "http://localhost:5000"),
        "incident": os.getenv("INCIDENT_SERVICE_URL", "http://localhost:5001"),
        "detection": os.getenv("DETECTION_SERVICE_URL", "http://localhost:5002"),
        "log_ingestion": os.getenv("LOG_INGESTION_URL", "http://localhost:5003"),
        "log_processing": os.getenv("LOG_PROCESSING_URL", "http://localhost:5004"),
    }


@pytest.fixture
def auth_token(api_base_urls):
    """Fixture to get authentication token"""
    auth_url = api_base_urls["auth"]
    try:
        response = requests.post(
            f"{auth_url}/login",
            json={"username": "testuser", "password": "testpass123"},
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("token")
    except Exception as e:
        print(f"Warning: Could not get auth token: {e}")
    return None


@pytest.fixture
def authorized_headers(auth_token):
    """Fixture providing authorization headers"""
    if auth_token:
        return {"Authorization": f"Bearer {auth_token}"}
    return {}


@pytest.fixture
def api_client(api_base_urls):
    """Fixture for making API requests"""
    class APIClient:
        def __init__(self, base_urls: Dict[str, str]):
            self.base_urls = base_urls
        
        def post(self, service: str, endpoint: str, **kwargs):
            """POST request to service endpoint"""
            url = f"{self.base_urls[service]}{endpoint}"
            return requests.post(url, **kwargs)
        
        def get(self, service: str, endpoint: str, **kwargs):
            """GET request to service endpoint"""
            url = f"{self.base_urls[service]}{endpoint}"
            return requests.get(url, **kwargs)
        
        def put(self, service: str, endpoint: str, **kwargs):
            """PUT request to service endpoint"""
            url = f"{self.base_urls[service]}{endpoint}"
            return requests.put(url, **kwargs)
        
        def delete(self, service: str, endpoint: str, **kwargs):
            """DELETE request to service endpoint"""
            url = f"{self.base_urls[service]}{endpoint}"
            return requests.delete(url, **kwargs)
    
    return APIClient(api_base_urls)


@pytest.fixture
def test_user_data():
    """Fixture providing test user data"""
    return {
        "valid": {
            "username": "testuser123",
            "email": "testuser@example.com",
            "password": "SecurePass123!"
        },
        "invalid": {
            "username": "",
            "email": "invalidemail",
            "password": "weak"
        }
    }


@pytest.fixture
def test_incident_data():
    """Fixture providing test incident data"""
    return {
        "valid": {
            "title": "Critical Database Connection Lost",
            "description": "Database connection failed",
            "severity": "critical",
            "source": "database_monitor",
            "environment": "production"
        },
        "invalid": {
            "title": "",
            "description": None,
            "severity": "unknown",
            "source": ""
        }
    }


@pytest.fixture
def test_log_data():
    """Fixture providing test log data"""
    return {
        "valid": {
            "logs": [
                {
                    "timestamp": "2026-04-12T10:00:00Z",
                    "level": "ERROR",
                    "service": "auth_service",
                    "message": "Failed login attempt",
                    "user_id": "user123"
                },
                {
                    "timestamp": "2026-04-12T10:00:05Z",
                    "level": "ERROR",
                    "service": "auth_service",
                    "message": "Failed login attempt",
                    "user_id": "user123"
                }
            ]
        },
        "empty": {"logs": []},
        "malformed": {"invalid_key": "data"}
    }


@pytest.fixture(scope="session")
def session_auth_token(api_base_urls):
    """Session-scoped fixture for auth token (used once per test session)"""
    auth_url = api_base_urls["auth"]
    try:
        response = requests.post(
            f"{auth_url}/login",
            json={"username": "sessionuser", "password": "sessionpass123"},
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("token")
    except Exception:
        pass
    return None
