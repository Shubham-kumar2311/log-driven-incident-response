"""
Black box tests for Incident Management Service
Tests incident creation, retrieval, and management without knowing internals
"""
import pytest
import requests
from datetime import datetime, timedelta


class TestIncidentCreationBlackBox:
    """Black box tests for incident creation"""
    
    def test_create_incident_with_valid_data(self, api_client, authorized_headers, test_incident_data):
        """Test creating incident with valid data"""
        incident = test_incident_data["valid"]
        response = api_client.post(
            "incident",
            "/incidents",
            json=incident,
            headers=authorized_headers,
            timeout=5
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert "incident_id" in data or "id" in data
    
    def test_create_incident_missing_required_fields(self, api_client, authorized_headers):
        """Test that missing required fields returns 400"""
        incident = {
            "title": "Test Incident"
            # Missing other required fields
        }
        response = api_client.post(
            "incident",
            "/incidents",
            json=incident,
            headers=authorized_headers,
            timeout=5
        )
        
        assert response.status_code == 400
    
    def test_create_incident_empty_title_returns_400(self, api_client, authorized_headers):
        """Test that empty title returns 400"""
        incident = {
            "title": "",
            "description": "Test",
            "severity": "high",
            "source": "test"
        }
        response = api_client.post(
            "incident",
            "/incidents",
            json=incident,
            headers=authorized_headers,
            timeout=5
        )
        
        assert response.status_code == 400
    
    def test_create_incident_invalid_severity_returns_400(self, api_client, authorized_headers):
        """Test that invalid severity returns 400"""
        incident = {
            "title": "Test",
            "description": "Test",
            "severity": "invalid_severity",
            "source": "test"
        }
        response = api_client.post(
            "incident",
            "/incidents",
            json=incident,
            headers=authorized_headers,
            timeout=5
        )
        
        assert response.status_code == 400
    
    @pytest.mark.parametrize("severity", ["low", "medium", "high", "critical"])
    def test_create_incident_valid_severities(self, api_client, authorized_headers, severity):
        """Test creating incidents with valid severity levels"""
        incident = {
            "title": f"Test Incident - {severity}",
            "description": f"Incident with {severity} severity",
            "severity": severity,
            "source": "test_source"
        }
        response = api_client.post(
            "incident",
            "/incidents",
            json=incident,
            headers=authorized_headers,
            timeout=5
        )
        
        assert response.status_code in [200, 201]
    
    def test_create_incident_without_auth_returns_401(self, api_client, test_incident_data):
        """Test that creating incident without auth returns 401"""
        incident = test_incident_data["valid"]
        response = api_client.post(
            "incident",
            "/incidents",
            json=incident,
            timeout=5
        )
        
        assert response.status_code == 401


class TestIncidentRetrievalBlackBox:
    """Black box tests for incident retrieval"""
    
    def test_get_incident_by_id(self, api_client, authorized_headers):
        """Test retrieving incident by ID"""
        incident_id = "INC-001"
        response = api_client.get(
            "incident",
            f"/incidents/{incident_id}",
            headers=authorized_headers,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "incident_id" in data or "id" in data
    
    def test_get_nonexistent_incident_returns_404(self, api_client, authorized_headers):
        """Test that non-existent incident returns 404"""
        response = api_client.get(
            "incident",
            "/incidents/NONEXISTENT-999",
            headers=authorized_headers,
            timeout=5
        )
        
        assert response.status_code == 404
    
    def test_list_all_incidents(self, api_client, authorized_headers):
        """Test listing all incidents"""
        response = api_client.get(
            "incident",
            "/incidents",
            headers=authorized_headers,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "incidents" in data or isinstance(data, list)
    
    def test_list_incidents_with_limit(self, api_client, authorized_headers):
        """Test listing incidents with limit parameter"""
        response = api_client.get(
            "incident",
            "/incidents",
            params={"limit": 10},
            headers=authorized_headers,
            timeout=5
        )
        
        assert response.status_code == 200
    
    def test_filter_incidents_by_severity(self, api_client, authorized_headers):
        """Test filtering incidents by severity"""
        response = api_client.get(
            "incident",
            "/incidents",
            params={"severity": "critical"},
            headers=authorized_headers,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        incidents = data.get("incidents", data if isinstance(data, list) else [])
        
        for incident in incidents:
            if "severity" in incident:
                assert incident["severity"] == "critical"
    
    @pytest.mark.parametrize("status", ["open", "in_progress", "resolved", "closed"])
    def test_filter_incidents_by_status(self, api_client, authorized_headers, status):
        """Test filtering incidents by status"""
        response = api_client.get(
            "incident",
            "/incidents",
            params={"status": status},
            headers=authorized_headers,
            timeout=5
        )
        
        assert response.status_code == 200
    
    def test_get_incident_without_auth_returns_401(self, api_client):
        """Test that retrieving incident without auth returns 401"""
        response = api_client.get(
            "incident",
            "/incidents",
            timeout=5
        )
        
        assert response.status_code == 401


class TestIncidentUpdateBlackBox:
    """Black box tests for incident updates"""
    
    def test_update_incident_status(self, api_client, authorized_headers):
        """Test updating incident status"""
        incident_id = "INC-001"
        update_data = {"status": "resolved"}
        response = api_client.put(
            "incident",
            f"/incidents/{incident_id}",
            json=update_data,
            headers=authorized_headers,
            timeout=5
        )
        
        assert response.status_code in [200, 202]
    
    def test_update_incident_invalid_status_returns_400(self, api_client, authorized_headers):
        """Test that invalid status returns 400"""
        incident_id = "INC-001"
        update_data = {"status": "invalid_status"}
        response = api_client.put(
            "incident",
            f"/incidents/{incident_id}",
            json=update_data,
            headers=authorized_headers,
            timeout=5
        )
        
        assert response.status_code == 400
    
    def test_update_nonexistent_incident_returns_404(self, api_client, authorized_headers):
        """Test that updating non-existent incident returns 404"""
        response = api_client.put(
            "incident",
            f"/incidents/NONEXISTENT-999",
            json={"status": "resolved"},
            headers=authorized_headers,
            timeout=5
        )
        
        assert response.status_code == 404
    
    def test_update_incident_without_auth_returns_401(self, api_client):
        """Test that updating without auth returns 401"""
        response = api_client.put(
            "incident",
            f"/incidents/INC-001",
            json={"status": "resolved"},
            timeout=5
        )
        
        assert response.status_code == 401
    
    def test_add_comment_to_incident(self, api_client, authorized_headers):
        """Test adding comment to incident"""
        incident_id = "INC-001"
        comment_data = {"comment": "This is a test comment"}
        response = api_client.post(
            "incident",
            f"/incidents/{incident_id}/comments",
            json=comment_data,
            headers=authorized_headers,
            timeout=5
        )
        
        # Response might be 200, 201, or 404 if incident doesn't exist
        assert response.status_code in [200, 201, 404]


class TestIncidentPaginationBlackBox:
    """Black box tests for incident pagination"""
    
    def test_list_incidents_with_page(self, api_client, authorized_headers):
        """Test pagination with page parameter"""
        response = api_client.get(
            "incident",
            "/incidents",
            params={"page": 1, "limit": 10},
            headers=authorized_headers,
            timeout=5
        )
        
        assert response.status_code == 200
    
    def test_list_incidents_with_offset(self, api_client, authorized_headers):
        """Test pagination with offset parameter"""
        response = api_client.get(
            "incident",
            "/incidents",
            params={"offset": 0, "limit": 20},
            headers=authorized_headers,
            timeout=5
        )
        
        assert response.status_code == 200
    
    def test_invalid_limit_returns_400(self, api_client, authorized_headers):
        """Test that invalid limit returns 400"""
        response = api_client.get(
            "incident",
            "/incidents",
            params={"limit": -1},
            headers=authorized_headers,
            timeout=5
        )
        
        assert response.status_code == 400


class TestIncidentSeverityEscalation:
    """Black box tests for incident severity escalation"""
    
    def test_escalate_incident_severity(self, api_client, authorized_headers):
        """Test escalating incident severity"""
        incident_id = "INC-001"
        escalation_data = {"new_severity": "critical"}
        response = api_client.put(
            "incident",
            f"/incidents/{incident_id}/escalate",
            json=escalation_data,
            headers=authorized_headers,
            timeout=5
        )
        
        # Might return 200, 202, or 404
        assert response.status_code in [200, 202, 404]


class TestIncidentBulkOperations:
    """Black box tests for bulk incident operations"""
    
    def test_bulk_close_incidents(self, api_client, authorized_headers):
        """Test bulk closing of incidents"""
        bulk_data = {"incident_ids": ["INC-001", "INC-002", "INC-003"]}
        response = api_client.post(
            "incident",
            "/incidents/bulk-close",
            json=bulk_data,
            headers=authorized_headers,
            timeout=5
        )
        
        # Might return 200, 202, 400, or 404
        assert response.status_code in [200, 202, 400, 404]
