# Black Box Testing Suite

This directory contains comprehensive black box tests for all microservices in the Log-Driven Incident Response system.

## Overview

Black box testing validates the external behavior of services without knowledge of internal implementation details. Tests focus on:
- **API Contracts**: Input validation, output format, HTTP status codes
- **Functionality**: Feature behavior as documented
- **Error Handling**: Proper error responses and recovery
- **Security**: Authorization, authentication, input validation
- **Performance**: Response times, batch processing

## Test Structure

```
tests/
├── conftest.py                                 # Shared fixtures and configuration
├── requirements_test.txt                       # Test dependencies
├── test_auth_service_blackbox.py              # Authentication service tests
├── test_incident_management_blackbox.py       # Incident management tests
├── test_detection_service_blackbox.py         # Detection service tests
└── test_log_ingestion_blackbox.py            # Log ingestion tests
```

## Setup

### 1. Install Dependencies

```bash
# From project root
pip install -r tests/requirements_test.txt

# Or install globally
pip install pytest pytest-cov pytest-mock requests python-dotenv
```

### 2. Configure Environment

Create a `.env` file in the project root or set environment variables:

```bash
# Service URLs (default to localhost)
AUTH_SERVICE_URL=http://localhost:5000
INCIDENT_SERVICE_URL=http://localhost:5001
DETECTION_SERVICE_URL=http://localhost:5002
LOG_INGESTION_URL=http://localhost:5003
LOG_PROCESSING_URL=http://localhost:5004
```

### 3. Start All Services

Before running tests, ensure all microservices are running:

```bash
# Start each service in separate terminal
cd src/auth_service && python app.py
cd src/incident_management && python app.py
cd src/detection_service && python app.py
cd src/log_ingestion_service && python app.py
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_auth_service_blackbox.py
pytest tests/test_incident_management_blackbox.py
pytest tests/test_detection_service_blackbox.py
pytest tests/test_log_ingestion_blackbox.py
```

### Run Specific Test Class

```bash
pytest tests/test_auth_service_blackbox.py::TestAuthServiceLoginBlackBox
pytest tests/test_incident_management_blackbox.py::TestIncidentCreationBlackBox
```

### Run Specific Test

```bash
pytest tests/test_auth_service_blackbox.py::TestAuthServiceLoginBlackBox::test_valid_login_returns_success
```

### Run with Verbose Output

```bash
pytest -v
pytest -vv  # More verbose
```

### Run with Coverage Report

```bash
pytest --cov=src --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`

### Run Tests in Parallel

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto
```

### Run Tests Matching Pattern

```bash
pytest -k "login"  # Run all tests with 'login' in name
pytest -k "not performance"  # Exclude performance tests
```

### Run with Different Markers

```bash
# Mark tests as slow
pytest -m "not slow"

# Run only slow tests
pytest -m slow
```

### Generate Test Report

```bash
# JUnit XML format
pytest --junit-xml=test_report.xml

# HTML report
pip install pytest-html
pytest --html=report.html
```

## Test Categories

### Authentication Service Tests
- **Login Tests**: Valid/invalid credentials, missing fields, edge cases
- **Registration Tests**: Valid/invalid data, duplicate users, validation
- **Token Validation**: Valid/invalid tokens, expiration
- **Error Handling**: Malformed requests, unsupported methods

### Incident Management Tests
- **Creation**: Valid/invalid data, required fields, severity validation
- **Retrieval**: Get by ID, list all, filtering by status/severity
- **Updates**: Status changes, invalid updates, non-existent incidents
- **Pagination**: Page navigation, limit handling, offset
- **Severity Escalation**: Escalating incidents
- **Bulk Operations**: Batch closing of incidents

### Detection Service Tests
- **Anomaly Detection**: Valid logs, empty logs, malformed data
- **Pattern Detection**: Brute force, error spikes
- **Rule Engine**: Getting rules, testing rules
- **ML Model**: Model info, performance metrics
- **Performance**: Large batch processing

### Log Ingestion Tests
- **Ingestion**: Single logs, batch ingestion, validation
- **File Watching**: Watching/unwatching files
- **Offset Tracking**: Getting/resetting offsets
- **Filtering**: By level, service, time range
- **Statistics**: Ingestion stats, health status
- **Parsing**: Structured and unstructured logs

## Fixtures

Shared fixtures in `conftest.py`:

### API Fixtures
- `api_client`: APIClient for making requests to services
- `api_base_urls`: Dictionary of service URLs
- `authorized_headers`: Headers with auth token
- `auth_token`: Authentication token

### Data Fixtures
- `test_user_data`: Valid and invalid user data
- `test_incident_data`: Valid and invalid incident data
- `test_log_data`: Valid and invalid log data

### Usage Example

```python
def test_example(api_client, authorized_headers, test_user_data):
    """Example test using fixtures"""
    response = api_client.post(
        "auth",
        "/login",
        json=test_user_data["valid"],
        headers=authorized_headers
    )
    assert response.status_code == 200
```

## Configuration

### Pytest Configuration (pytest.ini)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

### Environment Variables

- `AUTH_SERVICE_URL`: Auth service base URL
- `INCIDENT_SERVICE_URL`: Incident management service URL
- `DETECTION_SERVICE_URL`: Detection service URL
- `LOG_INGESTION_URL`: Log ingestion service URL
- `LOG_PROCESSING_URL`: Log processing service URL

## Test Development Guidelines

### 1. Naming Convention

```python
# Test file: test_<service>_blackbox.py
# Test class: Test<Feature>BlackBox
# Test method: test_<scenario>_<expected_result>

def test_valid_login_returns_token():
    """Test description"""
```

### 2. Testing Patterns

```python
# Arrange - Setup test data
user = {"username": "test", "password": "pass"}

# Act - Execute the action
response = api_client.post("auth", "/login", json=user)

# Assert - Verify the result
assert response.status_code == 200
```

### 3. Using Parametrize for Multiple Cases

```python
@pytest.mark.parametrize("username,password,expected_status", [
    ("user", "pass", 200),
    ("user", "wrong", 401),
    ("", "pass", 400),
])
def test_login_cases(api_client, username, password, expected_status):
    response = api_client.post(
        "auth", "/login",
        json={"username": username, "password": password}
    )
    assert response.status_code == expected_status
```

### 4. Handling Optional Endpoints

Some endpoints might not exist or might return 404. Use flexible assertions:

```python
assert response.status_code in [200, 404]  # Either success or not found
```

## Continuous Integration

Run tests in CI/CD pipeline:

```yaml
# GitHub Actions example
- name: Run Black Box Tests
  run: |
    pip install -r tests/requirements_test.txt
    pytest tests/ -v --junit-xml=results.xml --cov=src
```

## Troubleshooting

### Service Not Running

```
Error: Connection refused
Solution: Ensure all microservices are started before running tests
```

### Auth Token Not Available

```
Warning: Could not get auth token
Solution: Verify auth service is running and credentials are correct
```

### Timeout Errors

```
Error: Request timed out
Solution: Increase timeout value or check if service is responding
pytest --timeout=30  # Set timeout to 30 seconds
```

### Port Already in Use

```
Error: Address already in use
Solution: Kill process using the port or change service port
```

## Best Practices

1. **Independent Tests**: Each test should be independent and not rely on others
2. **Clear Names**: Test names should clearly describe what they test
3. **Single Responsibility**: Each test should verify one behavior
4. **No Hard Dependencies**: Avoid hardcoding test data or IDs
5. **Proper Cleanup**: Clean up resources after tests
6. **Meaningful Assertions**: Assert specific values, not just non-empty
7. **Document Complex Tests**: Add comments for complex test logic
8. **Use Fixtures**: Leverage pytest fixtures for reusable setup

## Adding New Tests

1. Create new test file: `test_<service>_blackbox.py`
2. Import fixtures from `conftest.py`
3. Write test classes and methods following naming convention
4. Run tests: `pytest tests/test_<service>_blackbox.py`
5. Check coverage: `pytest --cov=src tests/`

## Performance Testing

For performance benchmarking:

```bash
# Install pytest-benchmark
pip install pytest-benchmark

# Run with timing
pytest -v --durations=10

# Profile tests
pytest --profile tests/
```

## Documentation

For more information:
- [Pytest Documentation](https://docs.pytest.org/)
- [Requests Library](https://requests.readthedocs.io/)
- [Black Box Testing](https://en.wikipedia.org/wiki/Black-box_testing)
