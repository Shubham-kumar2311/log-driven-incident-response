# White Box Testing Suite

This directory contains comprehensive white box (glass box) tests for all microservices in the Log-Driven Incident Response system.

## Overview

White box testing examines the internal structure and logic of code, testing:
- **Internal Logic**: Algorithm implementation and business rules
- **Code Paths**: All branches and conditional logic
- **State Management**: Object state transitions and consistency
- **Data Processing**: Transformations and calculations
- **Error Handling**: Exception handling and edge cases
- **Performance**: Optimization and efficiency

## Test Structure

```
tests/
├── test_auth_service_whitebox.py              # 40+ authentication logic tests
├── test_incident_management_whitebox.py       # 50+ incident management tests
├── test_detection_service_whitebox.py         # 50+ detection algorithm tests
├── test_log_ingestion_whitebox.py            # 45+ log processing tests
└── whitebox_mocking_patterns.py               # Mocking pattern examples
```

## Setup

### 1. Install Dependencies

```bash
pip install -r tests/requirements_test.txt
```

Additional dependencies for white box testing:
- `pytest-mock` - Mocking framework
- `unittest.mock` - Standard Python mocking (included)
- `numpy` - For numerical computations in detection tests

### 2. Running Tests

```bash
# Run all white box tests
pytest tests/test_*_whitebox.py -v

# Run specific service tests
pytest tests/test_auth_service_whitebox.py -v

# Run specific test class
pytest tests/test_auth_service_whitebox.py::TestPasswordHashingLogic -v

# Run with coverage
pytest tests/test_*_whitebox.py --cov=src --cov-report=html
```

## Test Coverage by Service

### Authentication Service (40+ Tests)
- **Password Hashing**: Hash generation, verification, salt handling
- **Token Generation**: JWT creation, validation, expiration
- **User Model**: Data structure, serialization, sensitive data
- **Login Logic**: User lookup, password verification, failures
- **Registration**: Validation, duplication checks, strength requirements
- **Session Management**: Creation, invalidation, multi-device support
- **Middleware**: Token extraction, authorization checks

### Incident Management (50+ Tests)
- **Incident Creation**: Default values, unique ID generation, timestamps
- **State Transitions**: Valid/invalid status transfers, preventing invalid transitions
- **Severity Calculation**: Auto-escalation, threshold evaluation, level comparison
- **Correlation Logic**: Duplicate detection, incident merging, correlation weights
- **Filtering**: By severity, status, date range, combined criteria
- **Pagination**: Offset calculation, page slicing, partial pages
- **Comments**: Unique IDs, threading, ordering, editing
- **Metrics**: MTTR calculation, service breakdown, incident statistics

### Detection Service (50+ Tests)
- **Anomaly Detection Algorithms**:
  - Z-score calculations
  - Moving averages
  - Standard deviation detection
  - IQR-based detection
  - Rate of change detection
  - Isolation forest concept
- **Rule Engine**: Parsing, evaluation, complex conditions, priority ordering
- **Thresholds**: Definition, breach detection, dynamic adjustment, hysteresis
- **Log Parsing**: Timestamp extraction, level extraction, JSON/unstructured parsing
- **Feature Extraction**: Error counts, rates, response time stats, distributions
- **Anomaly Evaluation**: Confidence scoring, severity mapping, grouping
- **ML Integration**: Model predictions, feature normalization

### Log Ingestion (45+ Tests)
- **File Watching**: Initialization, state tracking, file rotation detection, reset logic
- **Offset Management**: Initialization, advancement, persistence, recovery, boundaries
- **Log Line Processing**: Reading from offset, incomplete line buffering, multiline logs
- **Log Batching**: Accumulation, flush timing, size limits, priority ordering
- **Error Handling**: Unreadable files, malformed JSON, encoding errors, large lines
- **Versioning**: Version tracking, duplicate detection, version numbering
- **Queue Management**: FIFO processing, priority reordering, overflow protection
- **Metrics**: Ingestion counts, latency, error rates, throughput

## White Box Testing Patterns

### 1. Testing Algorithm Implementations

```python
def test_zscore_calculation(self):
    """Test Z-score anomaly detection calculation"""
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]  # 100 is anomaly
    
    mean = np.mean(data)
    std = np.std(data)
    
    z_scores = [(x - mean) / std for x in data]
    
    anomalies = [x for i, x in enumerate(data) if abs(z_scores[i]) > 3]
    
    assert 100 in anomalies
```

### 2. Testing State Transitions

```python
def test_incident_transition_from_open_to_in_progress(self):
    """Test valid transition: OPEN -> IN_PROGRESS"""
    incident = {"status": IncidentStatus.OPEN}
    
    incident["status"] = IncidentStatus.IN_PROGRESS
    incident["updated_at"] = datetime.utcnow()
    
    assert incident["status"] == IncidentStatus.IN_PROGRESS
```

### 3. Testing with Mocks

```python
@patch('models.User.query')
def test_login_finds_user_by_username(self, mock_query):
    """Test that login logic queries user by username"""
    mock_user = Mock()
    mock_query.filter_by.return_value.first.return_value = mock_user
    
    user = mock_query.filter_by(username="testuser").first()
    
    assert user == mock_user
    mock_query.filter_by.assert_called_with(username="testuser")
```

### 4. Testing Data Transformations

```python
def test_feature_extraction_error_rate(self):
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
```

### 5. Testing Edge Cases

```python
def test_pagination_handles_last_partial_page(self):
    """Test pagination with incomplete last page"""
    incidents = [{"id": str(i)} for i in range(1, 26)]  # 25 items
    
    page = 3
    limit = 10
    offset = (page - 1) * limit
    
    result = incidents[offset:offset + limit]
    
    assert len(result) == 5  # Partial page
    assert result[0]["id"] == "21"
```

## Mocking Patterns

### Patching Functions

```python
@patch('module.function')
def test_with_patch(self, mock_func):
    mock_func.return_value = "mocked_value"
    # Test code
    mock_func.assert_called()
```

### Mocking External Dependencies

```python
@patch('requests.get')
def test_api_call(self, mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "value"}
    mock_get.return_value = mock_response
    
    # Test code
```

### Using Mock Objects

```python
def test_with_mock_object(self):
    mock_obj = Mock()
    mock_obj.method.return_value = "result"
    
    result = mock_obj.method()
    
    assert result == "result"
    mock_obj.method.assert_called_once()
```

## Test Execution Strategies

### Run by Complexity

```bash
# Quick unit tests (< 1 second each)
pytest tests/test_*_whitebox.py -v -k "simple"

# Complex algorithm tests
pytest tests/test_detection_service_whitebox.py -v -k "algorithm"

# Long-running tests
pytest tests/test_*_whitebox.py -v -m slow
```

### Run by Component

```bash
# Only authentication tests
pytest tests/test_auth_service_whitebox.py -v

# Only detection tests
pytest tests/test_detection_service_whitebox.py -v

# Only data processing tests
pytest tests/test_log_ingestion_whitebox.py -v
```

### Debugging Tests

```bash
# Run single test with detailed output
pytest tests/test_auth_service_whitebox.py::TestPasswordHashingLogic::test_verify_password_returns_true_for_matching -vv

# Show print statements
pytest tests/test_auth_service_whitebox.py -vv -s

# Drop into debugger on failure
pytest tests/test_auth_service_whitebox.py --pdb

# Show local variables in errors
pytest tests/test_auth_service_whitebox.py -l
```

## Coverage Analysis

### Generate Coverage Report

```bash
pytest tests/test_*_whitebox.py --cov=src --cov-report=html
```

### View Coverage Results

```bash
# Terminal report
pytest tests/test_*_whitebox.py --cov=src --cov-report=term-missing

# Open HTML report
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
xdg-open htmlcov/index.html # Linux
```

### Coverage Requirements

```bash
# Fail if coverage below 80%
pytest tests/test_*_whitebox.py --cov=src --cov-fail-under=80
```

## Key Differences: White Box vs Black Box

| Aspect | White Box | Black Box |
|--------|-----------|----------|
| **Focus** | Internal logic | External behavior |
| **Knowledge** | Needs code knowledge | No code knowledge needed |
| **Testing** | Individual functions | Complete workflows |
| **Mocking** | Heavy use of mocks | Minimal/no mocking |
| **Coverage** | Code branches | Use cases |
| **Examples** | Algorithm tests | API endpoint tests |

## Common Testing Scenarios

### 1. Testing Algorithm Correctness

```python
# Test that algorithm produces expected results
def test_algorithm_correctness(self):
    input_data = [...]
    expected_output = [...]
    
    actual_output = algorithm.process(input_data)
    
    assert actual_output == expected_output
```

### 2. Testing Boundary Conditions

```python
# Test edge values
def test_boundary_values(self):
    assert function(0) == expected_0
    assert function(1) == expected_1
    assert function(MAX_INT) == expected_max
    assert function(-1) == expected_negative
```

### 3. Testing Error Paths

```python
# Test error handling
def test_error_path(self):
    with pytest.raises(ValueError):
        function(invalid_input)
```

### 4. Testing State Changes

```python
# Test object state transitions
def test_state_change(self):
    obj = Object()
    assert obj.state == "initial"
    
    obj.transition()
    assert obj.state == "changed"
```

## Best Practices

### ✓ DO

- Test one logical unit per test
- Use descriptive test names
- Mock external dependencies
- Test both success and failure paths
- Use fixtures for shared setup
- Test boundary and edge cases
- Keep tests independent
- Use parametrization for similar tests

### ✗ DON'T

- Test implementation details only
- Create complex test setups
- Mock everything (some integration is good)
- Test multiple scenarios in one test
- Use hardcoded values
- Create interdependent tests
- Test external libraries

## Continuous Integration

### GitHub Actions Example

```yaml
- name: Run White Box Tests
  run: |
    pip install -r tests/requirements_test.txt
    pytest tests/test_*_whitebox.py -v --cov=src
```

### Coverage Report

Generate coverage badges and reports for CI/CD pipelines.

## Test Organization

Create test files for each service following the pattern:
- `test_<service>_whitebox.py` for white box tests
- `test_<service>_blackbox.py` for black box tests
- Separate concerns into test classes
- One feature/function group per class

## Extending Tests

To add new white box tests:

1. Create new test class: `TestNewFeature`
2. Add test methods: `def test_scenario_expected_result(self):`
3. Use mocks/patches for dependencies
4. Test both success and error paths
5. Run: `pytest tests/test_*_whitebox.py -v`

Example:

```python
class TestNewFeature:
    """Tests for new feature"""
    
    def test_feature_basic_functionality(self):
        """Test basic functionality"""
        # Arrange
        input_data = {...}
        
        # Act
        result = feature.process(input_data)
        
        # Assert
        assert result is not None
    
    def test_feature_with_mocked_dependency(self):
        """Test feature with mocked dependency"""
        with patch('module.dependency') as mock_dep:
            mock_dep.return_value = "mocked"
            
            result = feature.process()
            
            mock_dep.assert_called()
```

## Troubleshooting

### Import Errors

```bash
# Ensure src is in path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pytest tests/
```

### Mock Not Working

```python
# Use correct patch path (where it's used, not defined)
@patch('service.external_module')  # Where it's imported
def test_something(self, mock_module):
    pass
```

### Assertion Failures

```bash
# Run with verbose output and locals
pytest tests/test_file.py::TestClass::test_method -vv -l
```

## Performance Considerations

- Use fixtures for expensive operations
- Mock external API calls
- Consider test execution time
- Run slow tests separately
- Use parametrization instead of loops

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [White Box Testing Guide](https://en.wikipedia.org/wiki/White-box_testing)
- [Testing Best Practices](https://testingpython.com/)

## Summary

White box tests provide:
- ✅ Deep algorithmic validation
- ✅ Internal logic verification
- ✅ Edge case coverage
- ✅ Performance testing capability
- ✅ Regression prevention

Combined with black box tests, they ensure comprehensive quality assurance.
