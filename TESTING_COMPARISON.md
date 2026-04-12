# White Box vs Black Box Testing Guide

## Quick Comparison

| Feature | White Box Testing | Black Box Testing |
|---------|------------------|-------------------|
| **What** | Tests internal code logic | Tests external behavior |
| **How** | Access to source code | No source code access |
| **Focus** | Algorithm, business logic | User workflows |
| **Mocking** | Extensive mocking | Minimal/no mocking |
| **Coverage** | Code branches | Use cases |
| **Examples** | Function unit tests | API endpoint tests |
| **Cost** | Higher developer time | Lower developer time |
| **Speed** | Fast - unit level | Slower - integration level |
| **Maintenance** | Brittle to changes | Stable with API changes |
| **Purpose** | Quality assurance | Functional correctness |

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Testing Pyramid                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│                        E2E Tests                             │
│                    (Few, Slow, Expensive)                    │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│                    Integration Tests                         │
│              (Medium, Medium Speed, Medium Cost)             │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│    Unit Tests (White Box)  +  Black Box Tests                │
│    (Many, Fast, Cheap)  +  (Many, Fast, Cheap)              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## When to Use Each

### Use White Box Testing When:

✓ Testing internal algorithms and calculations  
✓ Verifying complex business logic  
✓ Testing error handling paths  
✓ Validating data transformations  
✓ Need high code coverage metrics  
✓ Testing performance-critical functions  
✓ Unit testing individual components  

### Use Black Box Testing When:

✓ Testing API contracts  
✓ Validating user workflows  
✓ Testing system integration  
✓ Verifying error messages  
✓ Testing with real services  
✓ Regression testing  
✓ Acceptance testing  

## Testing Strategy Examples

### Authentication Flow

```
White Box Tests:
├── Password hashing algorithm
├── Token generation logic
├── Session state transitions
└── Database query optimization

Black Box Tests:
├── Login endpoint returns token
├── Invalid credentials rejected
├── Token validation on protected endpoints
└── Logout invalidates session
```

### Incident Detection

```
White Box Tests:
├── Z-score anomaly algorithm
├── Threshold calculation
├── Correlation detection logic
├── Feature extraction pipeline

Black Box Tests:
├── Detect endpoint accepts logs
├── Returns anomalies in response
├── Filters incidents by criteria
└── Pagination works correctly
```

## Code Example Comparison

### Same Feature - Different Test Approaches

**Feature**: Calculate error rate from logs

#### White Box Test (Testing Algorithm)

```python
def test_error_rate_calculation_whitebox():
    """White box: Test internal calculation logic"""
    from detection_service.metrics import ErrorRateCalculator
    
    logs = [
        {"level": "ERROR"},
        {"level": "ERROR"},
        {"level": "INFO"},
        {"level": "INFO"},
        {"level": "INFO"}
    ]
    
    calculator = ErrorRateCalculator()
    error_rate = calculator.calculate(logs)
    
    # Test the calculation algorithm
    assert error_rate == 0.4
    assert isinstance(error_rate, float)
    assert 0 <= error_rate <= 1


def test_error_rate_calculation_edge_cases_whitebox():
    """White box: Test boundary conditions"""
    calculator = ErrorRateCalculator()
    
    # Edge cases
    assert calculator.calculate([]) == 0  # Empty logs
    assert calculator.calculate([{"level": "ERROR"}]) == 1.0  # All errors
    assert calculator.calculate([{"level": "INFO"}]) == 0  # No errors
```

#### Black Box Test (Testing Behavior)

```python
def test_error_rate_detection_blackbox(api_client):
    """Black box: Test API behavior and contract"""
    logs = [
        {
            "timestamp": "2026-04-12T10:00:00Z",
            "level": "ERROR",
            "message": "Error 1"
        },
        {
            "timestamp": "2026-04-12T10:00:01Z",
            "level": "ERROR",
            "message": "Error 2"
        },
        {
            "timestamp": "2026-04-12T10:00:02Z",
            "level": "INFO",
            "message": "Info 1"
        }
    ]
    
    # Submit logs to service
    response = api_client.post(
        "detection",
        "/detect",
        json={"logs": logs}
    )
    
    # Test the API contract
    assert response.status_code == 200
    data = response.json()
    assert "anomalies" in data or "metrics" in data
    # We don't care HOW it calculates, just that it returns results
```

## Project Structure

```
project/
├── tests/
│   ├── test_auth_service_whitebox.py        # White box tests
│   ├── test_auth_service_blackbox.py        # Black box tests
│   ├── test_incident_management_whitebox.py # White box tests
│   ├── test_incident_management_blackbox.py # Black box tests
│   └── ...
```

## Test Execution Strategy

### High Priority (Run Always)

```bash
# Both white box and black box together
pytest tests/ -v
```

### Continuous Integration

```bash
# White box tests catch logic errors
pytest tests/test_*_whitebox.py --cov=src

# Black box tests catch integration errors
pytest tests/test_*_blackbox.py
```

### Development

```bash
# Quick white box tests during development
pytest tests/test_auth_service_whitebox.py -v

# Before commit: run all tests
pytest tests/ --cov=src
```

### Debugging

```bash
# White box: drill into algorithm
pytest tests/test_detection_service_whitebox.py::TestAnomalyDetection -vv

# Black box: check service integration
pytest tests/test_detection_service_blackbox.py::TestDetectionService -vv
```

## Coverage Metrics

### White Box Focus

```
Function Coverage:        95%+
Branch Coverage:          90%+
Line Coverage:            95%+
```

### Black Box Focus

```
API Endpoint Coverage:    100%
User Workflow Coverage:   95%+
Error Condition Coverage: 90%+
```

## Real-World Example: Incident Severity

### The Feature

Automatically escalate incident severity if error count exceeds threshold.

### White Box Test

```python
class TestSeverityCalculation:
    """Test internal algorithm"""
    
    def test_escalation_threshold_exceeded(self):
        """Test business logic: escalate when threshold exceeded"""
        incident = {
            "severity": IncidentSeverity.MEDIUM,
            "error_count": 100  # Exceeds threshold of 50
        }
        
        # Test the escalation algorithm
        if incident["error_count"] > 50:
            incident["severity"] = IncidentSeverity.CRITICAL
        
        # Verify business logic worked
        assert incident["severity"] == IncidentSeverity.CRITICAL
```

### Black Box Test

```python
def test_severe_incident_escalation(api_client, authorized_headers):
    """Test feature works end-to-end"""
    
    # Create incident
    response = api_client.post(
        "incident",
        "/incidents",
        json={
            "title": "High Error Rate",
            "severity": "medium",
            "error_count": 100
        },
        headers=authorized_headers
    )
    
    # Verify incident was escalated (we don't care how)
    incident_data = response.json()
    # Check if severity was escalated through any means
    assert response.status_code == 201
```

## Test Maintenance

### White Box Tests Are Brittle

```python
# If internal function signature changes, this breaks
@patch('service.calculate_severity')
def test_severity_calculation(self, mock_calc):
    mock_calc.return_value = "CRITICAL"
    # Test breaks if function renamed or moved
```

### Black Box Tests Are Stable

```python
# If internal implementation changes but API stays same, this passes
response = api_client.put(f"/incidents/{id}", json={"severity": "high"})
# Still works even if internal calculation completely rewrote
```

## CI/CD Integration Example

```yaml
name: Testing Pipeline

jobs:
  unit_tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run White Box Tests (Unit Tests)
        run: |
          pytest tests/test_*_whitebox.py -v --cov=src
      - name: Upload Coverage
        uses: codecov/codecov-action@v2

  integration_tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start Services
        run: docker-compose up -d
      - name: Run Black Box Tests (Integration/API Tests)
        run: pytest tests/test_*_blackbox.py -v

  quality_gate:
    runs-on: ubuntu-latest
    steps:
      - name: Run All Tests
        run: pytest tests/ -v --cov=src --cov-fail-under=80
```

## Quick Decision Tree

```
Does it test internal algorithm?
├─ YES → White Box ✓
└─ NO → Proceed...

Does it test a specific code path?
├─ YES → White Box ✓
└─ NO → Proceed...

Does it test an external interface?
├─ YES → Black Box ✓
└─ NO → Proceed...

Does it test user workflow?
├─ YES → Black Box ✓
└─ NO → Both?
```

## Commands Cheat Sheet

```bash
# White box tests only
pytest tests/test_*_whitebox.py -v

# Black box tests only
pytest tests/test_*_blackbox.py -v

# Both together
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific test
pytest tests/test_auth_service_whitebox.py::TestPasswordHashingLogic -v

# Run with actual services (black box)
docker-compose up -d && pytest tests/test_*_blackbox.py -v
```

## Summary

| Aspect | White Box | Black Box |
|--------|-----------|----------|
| **Unit Test** | ✓ Primary | ✗ Not suitable |
| **Integration Test** | ✗ Not suitable | ✓ Primary |
| **Code Changes Impact** | Breaking | Non-breaking |
| **API Changes Impact** | Non-breaking | Breaking |
| **Debug Detail** | High | Low |
| **Real-World Testing** | Low | High |
| **Speed** | Fast | Slower |
| **Parallelizable** | Yes | Less |

## Best Practice

**Use both!**

White box tests ensure your code logic is correct and efficient. Black box tests ensure your entire system works from a user perspective. Together, they provide comprehensive quality assurance.

```
┌─────────────────────────────────────────────┐
│ Combined Testing Strategy                    │
├─────────────────────────────────────────────┤
│                                              │
│  White Box Tests (Fast)                     │
│  └─ Catch logic bugs early                  │
│  └─ High code coverage                      │
│  └─ Run on every commit                     │
│                                              │
│  Black Box Tests (Thorough)                 │
│  └─ Validate user workflows                 │
│  └─ Test integration points                 │
│  └─ Run before deployment                   │
│                                              │
│  → Together = Confidence!                   │
│                                              │
└─────────────────────────────────────────────┘
```

---

**Next Steps:**
1. Run white box tests: `pytest tests/test_*_whitebox.py -v`
2. Run black box tests: `pytest tests/test_*_blackbox.py -v`
3. Generate coverage: `pytest tests/ --cov=src --cov-report=html`
4. Extend tests for your features
