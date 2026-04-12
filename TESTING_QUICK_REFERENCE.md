# Quick Reference - Black Box Testing

## Installation
```bash
pip install -r tests/requirements_test.txt
```

## One-Liner Commands

### Run Tests
```bash
pytest                          # All tests
pytest -v                       # Verbose
pytest -k "auth"               # Keyword filter
pytest --co -q                 # Show test names only
```

### Run by Service
```bash
pytest tests/test_auth_service_blackbox.py
pytest tests/test_incident_management_blackbox.py
pytest tests/test_detection_service_blackbox.py
pytest tests/test_log_ingestion_blackbox.py
```

### Generate Reports
```bash
pytest --cov=src --cov-report=html        # Coverage HTML
pytest --junit-xml=results.xml            # JUnit XML
pytest -v --html=report.html              # HTML report
```

### Advanced
```bash
pytest -n auto                            # Parallel (requires pytest-xdist)
pytest --maxfail=3 -x                     # Stop after 3 failures
pytest -lf                                # Last failed tests
pytest --durations=10                     # Slowest 10 tests
pytest -m slow                            # Tests with @pytest.mark.slow
```

## Script Commands

### Windows
```bat
run_tests.bat all              # All tests
run_tests.bat auth             # Auth service
run_tests.bat coverage         # With coverage
run_tests.bat report           # HTML report
```

### Linux/Mac
```bash
./run_tests.sh all             # All tests
./run_tests.sh detection       # Detection service
./run_tests.sh coverage        # With coverage
./run_tests.sh parallel        # Parallel execution
```

## Configuration

### .env File
```bash
AUTH_SERVICE_URL=http://localhost:5000
INCIDENT_SERVICE_URL=http://localhost:5001
DETECTION_SERVICE_URL=http://localhost:5002
LOG_INGESTION_URL=http://localhost:5003
```

## Common Test Patterns

### Testing Success Path
```python
def test_valid_request(self, api_client):
    response = api_client.post("auth", "/login", 
                               json={"user": "test", "pass": "123"})
    assert response.status_code == 200
```

### Testing Error Path
```python
def test_invalid_request(self, api_client):
    response = api_client.post("auth", "/login", 
                               json={"user": "", "pass": ""})
    assert response.status_code == 400
```

### Using Fixtures
```python
def test_with_data(self, api_client, authorized_headers, test_user_data):
    response = api_client.post("auth", "/register",
                               json=test_user_data["valid"],
                               headers=authorized_headers)
    assert response.status_code in [200, 201]
```

### Parametrized Tests
```python
@pytest.mark.parametrize("status", ["open", "resolved"])
def test_statuses(self, api_client, status):
    response = api_client.get(f"/incidents/{status}")
    assert response.status_code == 200
```

## Available Fixtures

From `conftest.py`:
- `api_client` - APIClient instance
- `api_base_urls` - Service URLs dict
- `authorized_headers` - Auth headers
- `auth_token` - JWT token
- `test_user_data` - Sample user data
- `test_incident_data` - Sample incident data
- `test_log_data` - Sample log data

## Directory Structure

```
project/
├── tests/
│   ├── conftest.py                         # Fixtures
│   ├── test_auth_service_blackbox.py      # Auth tests
│   ├── test_incident_management_blackbox.py
│   ├── test_detection_service_blackbox.py
│   ├── test_log_ingestion_blackbox.py
│   ├── requirements_test.txt               # Dependencies
│   └── README.md                           # Full docs
├── pytest.ini                              # Configuration
├── .env.example                            # Environment template
├── run_tests.bat                           # Windows runner
├── run_tests.sh                            # Linux runner
└── TESTING_SUMMARY.md                      # Overview
```

## HTTP Status Codes to Test

```
200 OK              - Success
201 Created         - Resource created
202 Accepted        - Async accepted
400 Bad Request     - Invalid input
401 Unauthorized    - Auth required
403 Forbidden       - No permission
404 Not Found       - Resource missing
405 Method Not Allowed
409 Conflict        - Duplicate
500 Internal Error  - Server error
```

## Test Organization

### By File
- `test_auth_service_blackbox.py` - Authentication
- `test_incident_management_blackbox.py` - Incidents
- `test_detection_service_blackbox.py` - Detection
- `test_log_ingestion_blackbox.py` - Ingestion

### By Class
- `Test[Feature]BlackBox` - Always use this pattern
- One class per feature/endpoint group

### By Method
- `test_[scenario]_[expected_result]`
- Example: `test_valid_login_returns_token`

## Debugging

### See Request/Response
```python
print(response.status_code)
print(response.json())
print(response.text)
```

### Add Breakpoint
```python
def test_something(self, api_client):
    response = api_client.get(...)
    breakpoint()  # Debugger stops here
    assert response.status_code == 200
```

### Verbose Output
```bash
pytest -vv                    # Very verbose
pytest -s                     # Show print statements
pytest -s -v                  # Both
```

## Performance Testing

```bash
pytest --durations=10         # Show slowest 10 tests
pytest --benchmark           # Benchmark tests (needs pytest-benchmark)
```

## Coverage Targets

```bash
pytest --cov=src --cov-report=term-missing  # Show uncovered lines
pytest --cov=src --cov-report=html          # Generate HTML
pytest --cov=src --cov-fail-under=80        # Fail if <80%
```

## CI/CD Integration

### GitHub Actions
```yaml
- run: pytest tests/ -v --junit-xml=results.xml --cov=src
```

### GitLab CI
```yaml
test:
  script:
    - pip install -r tests/requirements_test.txt
    - pytest tests/ -v --junit-xml=results.xml
```

## Useful Markers

Test with markers:
```bash
pytest -m integration         # Only integration tests
pytest -m "not slow"         # Skip slow tests
pytest -m "auth or incident" # Multiple markers
```

Used in tests:
```python
@pytest.mark.slow
@pytest.mark.integration
def test_something():
    pass
```

## Terminal Commands Reference

```bash
# Install all
pip install -r tests/requirements_test.txt

# Run and stop on first failure
pytest -x

# Run last 3 failed tests
pytest --lf

# Run failed tests first
pytest --ff

# Show test names without running
pytest --collect-only

# Interactive mode
pytest -i

# Generate timing report
pytest --benchmark

# Clear cache
pytest --cache-clear
```

## Common Issues

| Issue | Solution |
|-------|----------|
| `ConnectionRefusedError` | Start services on correct ports |
| `Auth token not found` | Verify auth service URL and credentials |
| `Request timeout` | Increase timeout or check service |
| `Module not found` | `pip install -r tests/requirements_test.txt` |
| `401 Unauthorized` | Check `.env` file and service URLs |

## Tips & Tricks

1. **Run specific test**: `pytest -k test_name`
2. **Rerun failures**: `pytest --lf`
3. **Parallel tests**: `pytest -n auto` (install pytest-xdist)
4. **HTML reports**: `pytest --html=report.html`
5. **Coverage**: `pytest --cov=src --cov-report=html`
6. **Stop on N failures**: `pytest --maxfail=5`
7. **Show locals in errors**: `pytest -l`
8. **Capture output**: `pytest -s` (show print statements)

## Resources

- [Pytest Docs](https://docs.pytest.org/)
- [Requests Docs](https://requests.readthedocs.io/)
- [HTTP Status Codes](https://restfulapi.net/http-status-codes/)
- [Black Box Testing](https://en.wikipedia.org/wiki/Black-box_testing)

---

**Need more help?** Check `tests/README.md` for detailed documentation.
