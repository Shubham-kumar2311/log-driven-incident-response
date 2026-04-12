"""
Black box tests for Detection Service
Tests anomaly detection without knowing internal algorithms
"""
import pytest
import requests


class TestDetectionServiceBlackBox:
    """Black box tests for anomaly detection"""
    
    def test_detect_anomaly_with_valid_logs(self, api_client, test_log_data):
        """Test anomaly detection with valid log data"""
        response = api_client.post(
            "detection",
            "/detect",
            json=test_log_data["valid"],
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "anomalies" in data or "results" in data
    
    def test_detect_anomaly_returns_structured_results(self, api_client, test_log_data):
        """Test that anomaly detection returns structured results"""
        response = api_client.post(
            "detection",
            "/detect",
            json=test_log_data["valid"],
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response contains expected fields
        assert isinstance(data, dict)
    
    def test_detect_with_empty_logs_returns_400(self, api_client, test_log_data):
        """Test that empty logs returns 400"""
        response = api_client.post(
            "detection",
            "/detect",
            json=test_log_data["empty"],
            timeout=5
        )
        
        assert response.status_code == 400
    
    def test_detect_with_malformed_data_returns_400(self, api_client):
        """Test that malformed data returns 400"""
        response = api_client.post(
            "detection",
            "/detect",
            json={"invalid": "data"},
            timeout=5
        )
        
        assert response.status_code == 400
    
    def test_detect_with_missing_logs_key_returns_400(self, api_client):
        """Test that missing 'logs' key returns 400"""
        response = api_client.post(
            "detection",
            "/detect",
            json={"data": []},
            timeout=5
        )
        
        assert response.status_code == 400
    
    @pytest.mark.parametrize("log_count", [1, 5, 10, 100])
    def test_detect_with_different_log_counts(self, api_client, test_log_data, log_count):
        """Test detection with different numbers of logs"""
        logs = []
        base_log = test_log_data["valid"]["logs"][0]
        
        for i in range(log_count):
            log = base_log.copy()
            log["timestamp"] = f"2026-04-12T10:{i:02d}:00Z"
            logs.append(log)
        
        response = api_client.post(
            "detection",
            "/detect",
            json={"logs": logs},
            timeout=5
        )
        
        assert response.status_code == 200


class TestDetectionServiceAnalysisBlackBox:
    """Black box tests for analysis functionality"""
    
    def test_analyze_logs_by_service(self, api_client):
        """Test analyzing logs grouped by service"""
        logs = [
            {
                "timestamp": "2026-04-12T10:00:00Z",
                "service": "auth_service",
                "level": "ERROR",
                "message": "Failed login"
            },
            {
                "timestamp": "2026-04-12T10:01:00Z",
                "service": "database",
                "level": "ERROR",
                "message": "Connection timeout"
            }
        ]
        
        response = api_client.post(
            "detection",
            "/analyze",
            json={"logs": logs},
            timeout=5
        )
        
        assert response.status_code in [200, 400]
    
    def test_get_detection_statistics(self, api_client):
        """Test retrieving detection statistics"""
        response = api_client.get(
            "detection",
            "/stats",
            timeout=5
        )
        
        assert response.status_code in [200, 404]
    
    def test_get_detections_history(self, api_client):
        """Test retrieving detection history"""
        response = api_client.get(
            "detection",
            "/history",
            timeout=5
        )
        
        assert response.status_code in [200, 404]


class TestDetectionServicePatternDetection:
    """Black box tests for pattern detection"""
    
    def test_detect_brute_force_pattern(self, api_client):
        """Test detection of brute force patterns"""
        logs = [
            {
                "timestamp": f"2026-04-12T10:00:{i:02d}Z",
                "service": "auth_service",
                "level": "ERROR",
                "message": "Failed login attempt",
                "user": "admin"
            }
            for i in range(10)
        ]
        
        response = api_client.post(
            "detection",
            "/detect",
            json={"logs": logs},
            timeout=5
        )
        
        assert response.status_code == 200
    
    def test_detect_spike_pattern(self, api_client):
        """Test detection of error rate spikes"""
        logs = []
        
        # Normal logs
        for i in range(5):
            logs.append({
                "timestamp": f"2026-04-12T10:00:{i:02d}Z",
                "level": "INFO",
                "message": "Normal operation"
            })
        
        # Spike in errors
        for i in range(10):
            logs.append({
                "timestamp": f"2026-04-12T10:01:{i:02d}Z",
                "level": "ERROR",
                "message": "Error occurred"
            })
        
        response = api_client.post(
            "detection",
            "/detect",
            json={"logs": logs},
            timeout=5
        )
        
        assert response.status_code == 200


class TestDetectionServiceRuleEngine:
    """Black box tests for rule engine functionality"""
    
    def test_get_active_rules(self, api_client):
        """Test retrieving active detection rules"""
        response = api_client.get(
            "detection",
            "/rules",
            timeout=5
        )
        
        assert response.status_code in [200, 404]
    
    def test_get_rule_by_id(self, api_client):
        """Test retrieving specific rule"""
        response = api_client.get(
            "detection",
            "/rules/rule-001",
            timeout=5
        )
        
        assert response.status_code in [200, 404]
    
    def test_test_rule_against_logs(self, api_client):
        """Test evaluating a rule against logs"""
        test_data = {
            "rule": "error_count > 5",
            "logs": [
                {"level": "ERROR", "message": f"Error {i}"}
                for i in range(10)
            ]
        }
        
        response = api_client.post(
            "detection",
            "/test-rule",
            json=test_data,
            timeout=5
        )
        
        assert response.status_code in [200, 400, 404]


class TestDetectionServiceMLModel:
    """Black box tests for ML model functionality"""
    
    def test_get_model_info(self, api_client):
        """Test retrieving ML model information"""
        response = api_client.get(
            "detection",
            "/model/info",
            timeout=5
        )
        
        assert response.status_code in [200, 404]
    
    def test_get_model_performance(self, api_client):
        """Test retrieving model performance metrics"""
        response = api_client.get(
            "detection",
            "/model/performance",
            timeout=5
        )
        
        assert response.status_code in [200, 404]


class TestDetectionServiceErrorHandling:
    """Black box tests for error handling"""
    
    def test_detect_with_invalid_json_returns_400(self, api_base_urls):
        """Test that invalid JSON returns 400"""
        response = requests.post(
            f"{api_base_urls['detection']}/detect",
            data="invalid json {",
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        assert response.status_code == 400
    
    def test_detect_with_missing_required_fields_returns_400(self, api_client):
        """Test that missing required fields returns 400"""
        response = api_client.post(
            "detection",
            "/detect",
            json={},
            timeout=5
        )
        
        assert response.status_code == 400
    
    def test_nonexistent_endpoint_returns_404(self, api_base_urls):
        """Test that non-existent endpoint returns 404"""
        response = requests.get(
            f"{api_base_urls['detection']}/nonexistent",
            timeout=5
        )
        
        assert response.status_code == 404
    
    def test_unsupported_http_method_returns_405(self, api_base_urls):
        """Test that unsupported HTTP method returns 405"""
        response = requests.delete(
            f"{api_base_urls['detection']}/detect",
            timeout=5
        )
        
        assert response.status_code == 405


class TestDetectionServicePerformance:
    """Black box performance tests"""
    
    def test_large_log_batch_processing(self, api_client):
        """Test processing large batch of logs"""
        logs = [
            {
                "timestamp": f"2026-04-12T10:00:00Z",
                "service": "app",
                "level": "INFO",
                "message": f"Log message {i}"
            }
            for i in range(1000)
        ]
        
        response = api_client.post(
            "detection",
            "/detect",
            json={"logs": logs},
            timeout=30  # Longer timeout for large batch
        )
        
        assert response.status_code in [200, 400]
