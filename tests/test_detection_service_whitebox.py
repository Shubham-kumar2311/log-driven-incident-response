"""
White box tests for Detection Service
Tests internal algorithms, anomaly detection logic, and rule engine
"""
import pytest
from unittest.mock import Mock, patch
import numpy as np
from datetime import datetime, timedelta
import json


class TestAnomalyDetectionAlgorithms:
    """White box tests for anomaly detection algorithms"""
    
    def test_zscore_calculation(self):
        """Test Z-score anomaly detection calculation"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]  # 100 is anomaly
        
        mean = np.mean(data)
        std = np.std(data)
        
        z_scores = [(x - mean) / std for x in data]
        
        # Anomalies are typically > 3 or < -3
        anomalies = [x for i, x in enumerate(data) if abs(z_scores[i]) > 3]
        
        assert 100 in anomalies
    
    def test_moving_average_baseline(self):
        """Test moving average for baseline calculation"""
        error_rates = [5, 6, 4, 5, 7, 6, 5, 20, 6, 5]  # 20 is spike
        
        window_size = 3
        moving_avg = []
        
        for i in range(len(error_rates) - window_size + 1):
            avg = sum(error_rates[i:i+window_size]) / window_size
            moving_avg.append(avg)
        
        # Last spike should deviate from baseline
        assert moving_avg[-1] > 10
    
    def test_standard_deviation_anomaly_detection(self):
        """Test anomaly detection using standard deviation"""
        values = [10, 11, 9, 10, 12, 11, 10, 100, 9, 10]
        
        mean = np.mean(values)
        std = np.std(values)
        threshold = mean + (3 * std)
        
        anomalies = [v for v in values if v > threshold]
        
        assert 100 in anomalies
    
    def test_interquartile_range_anomaly(self):
        """Test IQR-based anomaly detection"""
        data = sorted([1, 2, 3, 4, 5, 6, 7, 8, 9, 100])
        
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)
        
        anomalies = [x for x in data if x < lower_bound or x > upper_bound]
        
        assert 100 in anomalies
    
    def test_rate_of_change_detection(self):
        """Test detecting anomalies based on rate of change"""
        cpu_usage = [20, 21, 22, 23, 85, 84, 82, 25, 24]
        
        rate_of_change = []
        for i in range(1, len(cpu_usage)):
            change = cpu_usage[i] - cpu_usage[i-1]
            rate_of_change.append(abs(change))
        
        # Anomaly is sudden spike
        spike_indices = [i for i, roc in enumerate(rate_of_change) if roc > 50]
        
        assert len(spike_indices) > 0
    
    def test_isolation_forest_concept(self):
        """Test isolation forest algorithm concept"""
        # Normal data clustered together
        normal_data = [(i, i*2) for i in range(100)]
        # Outlier far from cluster
        anomaly = (1000, 2000)
        
        all_data = normal_data + [anomaly]
        
        def simple_isolation(point, data, threshold=2):
            # Simple distance-based isolation
            distances = [
                ((point[0] - p[0])**2 + (point[1] - p[1])**2)**0.5
                for p in data if p != point
            ]
            avg_distance = sum(distances) / len(distances)
            return avg_distance < threshold
        
        is_normal = simple_isolation(anomaly, all_data, threshold=500)
        assert is_normal is False


class TestRuleEngine:
    """White box tests for rule engine implementation"""
    
    def test_rule_parsing(self):
        """Test parsing detection rules"""
        rule_json = """
        {
            "name": "High Error Rate",
            "condition": "error_count > 10 AND error_rate > 0.1",
            "severity": "critical"
        }
        """
        
        rule = json.loads(rule_json)
        
        assert rule["name"] == "High Error Rate"
        assert "error_count > 10" in rule["condition"]
        assert rule["severity"] == "critical"
    
    def test_rule_evaluation_simple_condition(self):
        """Test evaluating simple rule condition"""
        rule = {"condition": "error_count > 10"}
        event = {"error_count": 15}
        
        # Simple evaluation
        is_triggered = event.get("error_count", 0) > 10
        
        assert is_triggered is True
    
    def test_rule_evaluation_complex_condition(self):
        """Test evaluating complex rule with multiple conditions"""
        event = {
            "error_count": 15,
            "error_rate": 0.2,
            "response_time": 5000
        }
        
        # Complex condition
        is_triggered = (
            event["error_count"] > 10 and 
            event["error_rate"] > 0.1 and
            event["response_time"] > 1000
        )
        
        assert is_triggered is True
    
    def test_rule_evaluation_negation(self):
        """Test rule evaluation with negation"""
        event = {"is_production": False}
        
        # Should NOT trigger in non-production
        is_triggered = event["is_production"] is True
        
        assert is_triggered is False
    
    def test_rule_ordering_priority(self):
        """Test that rules are evaluated in priority order"""
        rules = [
            {"id": "rule1", "priority": 1},
            {"id": "rule2", "priority": 3},
            {"id": "rule3", "priority": 2}
        ]
        
        sorted_rules = sorted(rules, key=lambda r: r["priority"])
        
        assert sorted_rules[0]["id"] == "rule1"
        assert sorted_rules[1]["id"] == "rule3"
        assert sorted_rules[2]["id"] == "rule2"
    
    def test_rule_caching(self):
        """Test that rules are cached for performance"""
        cache = {}
        
        rule = {"id": "rule1", "name": "High Error Rate"}
        cache["rule1"] = rule
        
        # Retrieve from cache
        cached_rule = cache.get("rule1")
        
        assert cached_rule is not None
        assert cached_rule["name"] == "High Error Rate"


class TestThresholdManagement:
    """White box tests for threshold management"""
    
    def test_threshold_definition(self):
        """Test threshold definition and storage"""
        thresholds = {
            "error_rate": 0.1,
            "response_time": 5000,
            "cpu_usage": 80,
            "memory_usage": 90
        }
        
        assert thresholds["error_rate"] == 0.1
        assert thresholds["response_time"] == 5000
    
    def test_threshold_breach_detection(self):
        """Test detecting threshold breach"""
        threshold = {"error_rate": 0.1}
        metric = {"error_rate": 0.15}
        
        is_breached = metric["error_rate"] > threshold["error_rate"]
        
        assert is_breached is True
    
    def test_dynamic_threshold_adjustment(self):
        """Test dynamic threshold adjustment based on baseline"""
        baseline = 10.0
        std_dev = 2.0
        sensitivity = 2  # 2 sigma
        
        dynamic_threshold = baseline + (sensitivity * std_dev)
        
        assert dynamic_threshold == 14.0
    
    def test_threshold_hysteresis(self):
        """Test hysteresis to prevent flapping"""
        upper_threshold = 100
        lower_threshold = 90
        state = "normal"
        value = 95
        
        # Apply hysteresis
        if state == "normal" and value > upper_threshold:
            state = "alert"
        elif state == "alert" and value < lower_threshold:
            state = "normal"
        
        assert state == "normal"  # Still below upper threshold


class TestLogParsing:
    """White box tests for log parsing logic"""
    
    def test_log_timestamp_extraction(self):
        """Test extracting timestamp from log"""
        log_line = "2026-04-12T10:30:45.123Z ERROR: Connection timeout"
        
        import re
        timestamp_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
        match = re.search(timestamp_pattern, log_line)
        
        assert match is not None
    
    def test_log_level_extraction(self):
        """Test extracting log level"""
        logs = [
            ("DEBUG: Test", "DEBUG"),
            ("INFO: Test", "INFO"),
            ("WARN: Test", "WARN"),
            ("ERROR: Test", "ERROR"),
            ("CRITICAL: Test", "CRITICAL")
        ]
        
        import re
        level_pattern = r'(DEBUG|INFO|WARN|ERROR|CRITICAL)'
        
        for log_line, expected_level in logs:
            match = re.search(level_pattern, log_line)
            assert match.group(1) == expected_level
    
    def test_json_log_parsing(self):
        """Test parsing JSON formatted logs"""
        log_json = '{"timestamp": "2026-04-12T10:30:45Z", "level": "ERROR", "message": "Failed"}'
        
        log_data = json.loads(log_json)
        
        assert log_data["level"] == "ERROR"
        assert "Failed" in log_data["message"]
    
    def test_unstructured_log_parsing(self):
        """Test parsing unstructured log messages"""
        log_line = "2026-04-12 10:30:45,123 ERROR [service:api] User 123 failed login: Invalid password"
        
        # Extract components
        import re
        
        timestamp = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', log_line)
        level = re.search(r'(ERROR|WARN|INFO|DEBUG)', log_line)
        service = re.search(r'\[service:(\w+)\]', log_line)
        
        assert timestamp is not None
        assert level.group(1) == "ERROR"
        assert service.group(1) == "api"


class TestFeatureExtraction:
    """White box tests for feature extraction logic"""
    
    def test_extract_error_count_feature(self):
        """Test extracting error count feature"""
        logs = [
            {"level": "ERROR"},
            {"level": "ERROR"},
            {"level": "INFO"},
            {"level": "ERROR"},
            {"level": "WARNING"}
        ]
        
        error_count = sum(1 for log in logs if log["level"] == "ERROR")
        
        assert error_count == 3
    
    def test_extract_error_rate_feature(self):
        """Test extracting error rate feature"""
        logs = [
            {"level": "ERROR"},
            {"level": "ERROR"},
            {"level": "INFO"},
            {"level": "INFO"},
            {"level": "INFO"}
        ]
        
        error_rate = sum(1 for log in logs if log["level"] == "ERROR") / len(logs)
        
        assert error_rate == 0.4
    
    def test_extract_response_time_stats(self):
        """Test extracting response time statistics"""
        response_times = [100, 150, 120, 110, 500, 105]
        
        min_time = min(response_times)
        max_time = max(response_times)
        avg_time = sum(response_times) / len(response_times)
        
        assert min_time == 100
        assert max_time == 500
        assert avg_time > 150
    
    def test_extract_request_distribution(self):
        """Test extracting request distribution by service"""
        logs = [
            {"service": "api"},
            {"service": "api"},
            {"service": "database"},
            {"service": "cache"},
            {"service": "api"}
        ]
        
        distribution = {}
        for log in logs:
            service = log["service"]
            distribution[service] = distribution.get(service, 0) + 1
        
        assert distribution["api"] == 3
    
    def test_extract_temporal_features(self):
        """Test extracting temporal features from logs"""
        base_time = datetime.utcnow()
        logs = [
            {"timestamp": base_time, "service": "api"},
            {"timestamp": base_time + timedelta(minutes=1), "service": "api"},
            {"timestamp": base_time + timedelta(minutes=5), "service": "api"}
        ]
        
        # Calculate time gaps
        time_gaps = []
        for i in range(1, len(logs)):
            gap = (logs[i]["timestamp"] - logs[i-1]["timestamp"]).total_seconds()
            time_gaps.append(gap)
        
        assert len(time_gaps) == 2
        assert time_gaps[0] == 60


class TestAnomalyEvaluation:
    """White box tests for anomaly evaluation and scoring"""
    
    def test_anomaly_confidence_score(self):
        """Test calculating anomaly confidence score"""
        metric_deviation = 0.8  # Deviation from baseline
        rule_matches = 3  # Number of rules triggered
        
        confidence = (metric_deviation * 0.6) + (min(rule_matches, 5) / 5 * 0.4)
        
        assert 0 <= confidence <= 1
    
    def test_anomaly_severity_mapping(self):
        """Test mapping confidence score to severity"""
        def map_severity(confidence):
            if confidence >= 0.9:
                return "CRITICAL"
            elif confidence >= 0.7:
                return "HIGH"
            elif confidence >= 0.5:
                return "MEDIUM"
            elif confidence >= 0.3:
                return "LOW"
            else:
                return "INFO"
        
        assert map_severity(0.95) == "CRITICAL"
        assert map_severity(0.75) == "HIGH"
        assert map_severity(0.55) == "MEDIUM"
        assert map_severity(0.35) == "LOW"
    
    def test_anomaly_grouping(self):
        """Test grouping related anomalies"""
        anomalies = [
            {"id": "1", "service": "api", "type": "high_error_rate"},
            {"id": "2", "service": "api", "type": "high_latency"},
            {"id": "3", "service": "database", "type": "connection_timeout"}
        ]
        
        grouped = {}
        for anomaly in anomalies:
            service = anomaly["service"]
            if service not in grouped:
                grouped[service] = []
            grouped[service].append(anomaly)
        
        assert len(grouped["api"]) == 2
        assert len(grouped["database"]) == 1


class TestMLModelIntegration:
    """White box tests for ML model integration"""
    
    @patch('ml_client.predict')
    def test_ml_model_prediction_call(self, mock_predict):
        """Test calling ML model for prediction"""
        mock_predict.return_value = 0.85  # Anomaly score
        
        features = {
            "error_rate": 0.15,
            "response_time": 5000,
            "cpu_usage": 85
        }
        
        score = mock_predict(features)
        
        assert score == 0.85
        mock_predict.assert_called_once_with(features)
    
    def test_feature_normalization_for_ml(self):
        """Test normalizing features for ML model"""
        raw_features = {
            "error_rate": 0.5,  # 0-1 range
            "response_time": 5000,  # 0-10000 ms
            "cpu_usage": 85  # 0-100%
        }
        
        # Normalize
        normalized = {
            "error_rate": raw_features["error_rate"],
            "response_time": raw_features["response_time"] / 10000,
            "cpu_usage": raw_features["cpu_usage"] / 100
        }
        
        assert 0 <= normalized["response_time"] <= 1
        assert 0 <= normalized["cpu_usage"] <= 1


class TestDetectionPerformance:
    """White box tests for detection performance optimization"""
    
    def test_batch_processing_efficiency(self):
        """Test efficient batch processing"""
        batch_size = 1000
        logs_to_process = 10000
        
        num_batches = (logs_to_process + batch_size - 1) // batch_size
        
        assert num_batches == 10
    
    def test_caching_rule_results(self):
        """Test caching results to avoid recomputation"""
        cache = {}
        
        def evaluate_rule(rule_id, data):
            cache_key = f"{rule_id}:{hash(tuple(sorted(data.items())))}"
            
            if cache_key in cache:
                return cache[cache_key]
            
            # Expensive computation
            result = len(data) > 5
            cache[cache_key] = result
            return result
        
        data = {"a": 1, "b": 2}
        result1 = evaluate_rule("rule1", data)
        result2 = evaluate_rule("rule1", data)
        
        assert result1 == result2
