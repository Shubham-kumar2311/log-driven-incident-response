# Complete Testing Reference - Black Box + White Box

## Executive Summary

Your project now has:
- ✅ **110+ Black Box Tests** (API/integration testing)
- ✅ **185+ White Box Tests** (unit/logic testing)
- ✅ **295 Total Tests** providing complete coverage
- ✅ **Multiple Documentation Guides**
- ✅ **CI/CD Ready Infrastructure**

---

## Quick Start (5 minutes)

### 1. Install Dependencies
```bash
pip install -r tests/requirements_test.txt
```

### 2. Run All Tests
```bash
# White box (unit tests) - FAST (~30 seconds)
pytest tests/test_*_whitebox.py -v

# OR with coverage
pytest tests/test_*_whitebox.py --cov=src --cov-report=term
```

### 3. View Results
```bash
# Should see: passed 185+ tests in less than 1 minute
```

---

## Testing Overview

### Black Box Testing (API/Integration)
- **What**: Tests external behavior and API contracts
- **Where**: `tests/test_*_blackbox.py`
- **Tests**: 110+ (25 auth, 30 incident, 25 detection, 30 ingestion)
- **Requires**: Services running on localhost
- **Speed**: Slower (network calls)
- **Purpose**: Validate workflows and system integration

### White Box Testing (Unit/Logic)
- **What**: Tests internal algorithms and business logic
- **Where**: `tests/test_*_whitebox.py`
- **Tests**: 185+ (40 auth, 50 incident, 50 detection, 45 ingestion)
- **Requires**: Only test dependencies (mocked)
- **Speed**: Fast (<1 second per test)
- **Purpose**: Catch logical errors early

---

## Common Commands

### Run All Tests
```bash
# Run everything (fast + slow)
pytest tests/ -v

# Run only white box (fast, no services needed)
pytest tests/test_*_whitebox.py -v

# Run only black box (slow, needs services running)
pytest tests/test_*_blackbox.py -v
```

### Generate Reports
```bash
# Coverage report (HTML)
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html

# JUnit XML (for CI/CD)
pytest tests/ --junit-xml=results.xml

# Terminal coverage
pytest tests/ --cov=src --cov-report=term-missing
```

### Run Specific Services
```bash
# Auth service only
pytest tests/test_auth_service_whitebox.py -v
pytest tests/test_auth_service_blackbox.py -v

# Incident management only
pytest tests/test_incident_management_whitebox.py -v
pytest tests/test_incident_management_blackbox.py -v

# Detection service only
pytest tests/test_detection_service_whitebox.py -v
pytest tests/test_detection_service_blackbox.py -v

# Log ingestion only
pytest tests/test_log_ingestion_whitebox.py -v
pytest tests/test_log_ingestion_blackbox.py -v
```

### Debugging & Development
```bash
# Run with verbose output
pytest tests/ -vv

# Show print statements
pytest tests/ -s

# Stop at first failure
pytest tests/ -x

# Show slowest tests
pytest tests/ --durations=10

# Drop into debugger on failure
pytest tests/ --pdb

# Run only failed tests
pytest tests/ --lf

# Run failed tests first
pytest tests/ --ff
```

### Filter Tests
```bash
# Run tests matching keyword
pytest tests/ -k "password" -v

# Run tests matching pattern
pytest tests/ -k "auth and not middleware" -v

# Exclude tests
pytest tests/ -k "not slow" -v

# Run specific test class
pytest tests/test_auth_service_whitebox.py::TestPasswordHashingLogic -v

# Run specific test method
pytest tests/test_auth_service_whitebox.py::TestPasswordHashingLogic::test_verify_password_returns_true_for_matching -v
```

### Performance
```bash
# Show timing for each test
pytest tests/ --durations=0

# Show 10 slowest tests
pytest tests/ --durations=10 -q

# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest tests/ -n auto
```

---

## File Guide

### Core Test Files

| File | Type | Tests | Focus |
|------|------|-------|-------|
| test_auth_service_whitebox.py | Unit | 40+ | Password hashing, JWT, sessions |
| test_auth_service_blackbox.py | API | 25+ | Login, register, middleware |
| test_incident_management_whitebox.py | Unit | 50+ | States, correlation, metrics |
| test_incident_management_blackbox.py | API | 30+ | CRUD, filtering, escalation |
| test_detection_service_whitebox.py | Unit | 50+ | Algorithms, rules, features |
| test_detection_service_blackbox.py | API | 25+ | Detection, analysis, ML |
| test_log_ingestion_whitebox.py | Unit | 45+ | File watching, offsets, batching |
| test_log_ingestion_blackbox.py | API | 30+ | Ingestion, filtering, stats |

### Configuration Files

| File | Purpose |
|------|---------|
| pytest.ini | Pytest configuration, markers |
| .env.example | Service URLs template |
| tests/requirements_test.txt | Test dependencies |
| conftest.py | Shared fixtures |

### Documentation

| File | Content |
|------|---------|
| tests/README.md | Black box testing guide |
| tests/WHITEBOX_README.md | White box testing guide |
| TESTING_SUMMARY.md | Black box overview |
| WHITEBOX_TESTING_SUMMARY.md | White box overview |
| TESTING_COMPARISON.md | White box vs Black box |
| TESTING_QUICK_REFERENCE.md | Command reference |
| COMPLETE_TESTING_REFERENCE.md | This file |

### Scripts

| File | Platform |
|------|----------|
| run_tests.bat | Windows |
| run_tests.sh | Linux/Mac |

---

## Setup Guide

### Step 1: Install Dependencies
```bash
pip install -r tests/requirements_test.txt
```

### Step 2: Configure Environment (Optional)
```bash
# Copy environment template
cp .env.example .env

# Edit .env if services are on different ports
# Default assumes localhost with standard ports
```

### Step 3a: Run White Box Tests (No Services Needed)
```bash
pytest tests/test_*_whitebox.py -v
# Should complete in < 1 minute
```

### Step 3b: Run Black Box Tests (Services Required)
```bash
# Start services first
cd src/auth_service && python app.py &
cd src/incident_management && python app.py &
cd src/detection_service && python app.py &
cd src/log_ingestion_service && python app.py &

# Then run tests
pytest tests/test_*_blackbox.py -v
```

### Step 4: View Coverage
```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

---

## Test Structure

### White Box (Unit Tests)

```python
# Test internal algorithm
def test_zscore_anomaly_detection():
    data = [1, 2, 3, ..., 100]  # 100 is anomaly
    
    mean = np.mean(data)
    std = np.std(data)
    z_scores = [(x - mean) / std for x in data]
    
    anomalies = [x for i, x in enumerate(data) 
                 if abs(z_scores[i]) > 3]
    
    assert 100 in anomalies
```

### Black Box (API Tests)

```python
# Test API endpoint
def test_detect_anomaly_with_valid_logs(api_client):
    logs = [{"level": "INFO"}, {"level": "ERROR"}, ...]
    
    response = api_client.post(
        "detection",
        "/detect",
        json={"logs": logs}
    )
    
    assert response.status_code == 200
    assert "anomalies" in response.json()
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      
      - name: Install dependencies
        run: pip install -r tests/requirements_test.txt
      
      - name: Run white box tests
        run: |
          pytest tests/test_*_whitebox.py \
            --cov=src \
            --cov-report=xml \
            --junit-xml=whitebox.xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          files: ./coverage.xml
```

### GitLab CI

```yaml
test:
  stage: test
  script:
    - pip install -r tests/requirements_test.txt
    - pytest tests/test_*_whitebox.py --cov=src
    - pytest tests/test_*_blackbox.py --junit-xml=results.xml
  artifacts:
    reports:
      junit: results.xml
```

---

## Decision Tree: Which Tests to Run?

```
Are you developing?
├─ YES → Run white box: pytest tests/test_*_whitebox.py -v
└─ NO → Proceed...

Before committing?
├─ YES → Run all: pytest tests/ -v
└─ NO → Proceed...

Before deploying?
├─ YES → Run with coverage: pytest tests/ --cov=src --cov-fail-under=80
└─ NO → Proceed...

Debugging specific service?
├─ YES → Run that service: pytest tests/test_<service>_* -vv -s
└─ NO → Run all tests
```

---

## Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'pytest'"
**Solution:**
```bash
pip install -r tests/requirements_test.txt
```

### Issue: "Connection refused" (Black Box)
**Solution:**
```bash
# Make sure services are running
ps aux | grep python

# Or start manually
cd src/auth_service && python app.py
```

### Issue: Test takes too long
**Solution:**
```bash
# Run only white box (fast)
pytest tests/test_*_whitebox.py -v

# Or run with timeout
pytest tests/ --timeout=10
```

### Issue: Coverage report not generated
**Solution:**
```bash
# Install coverage tools
pip install pytest-cov

# Generate report
pytest tests/ --cov=src --cov-report=html --cov-report=term
```

---

## Test Naming Convention

### Test File Names
```
test_<service>_whitebox.py   # Unit tests (logic)
test_<service>_blackbox.py   # API tests (integration)
```

### Test Class Names
```
Test<Feature>WhiteBox        # Unit test class
Test<Feature>BlackBox        # API test class
```

### Test Method Names
```
test_<scenario>_<expected>   # Descriptive name

Examples:
test_valid_login_returns_token
test_invalid_password_returns_401
test_zscore_calculation_detects_outliers
test_incident_transition_from_open_to_resolved
```

---

## Performance Benchmark

### Expected Test Execution Times

```
White Box Tests (185 tests):
├─ Password hashing (8 tests) ........... ~0.5 seconds
├─ Incident logic (50 tests) ........... ~2 seconds
├─ Detection algorithms (50 tests) .... ~3 seconds
├─ Log ingestion (45 tests) ........... ~1 second
└─ Total: ~6 seconds

Black Box Tests (110 tests):
├─ Auth endpoints (25 tests) .......... ~10 seconds
├─ Incident endpoints (30 tests) ..... ~15 seconds
├─ Detection endpoints (25 tests) .... ~10 seconds
├─ Ingestion endpoints (30 tests) .... ~10 seconds
└─ Total: ~45 seconds (requires services)

All Tests: ~51 seconds total
```

---

## Coverage Goals

### Code Coverage Targets

```
White Box Tests:
├─ Function Coverage ............... 95%+
├─ Branch Coverage ................ 90%+
└─ Line Coverage .................. 95%+

Overall Goal: 80%+ Code Coverage
```

### Coverage Command

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=html --cov-fail-under=80

# View in browser
open htmlcov/index.html
```

---

## Extending Tests

### Adding White Box Test

```python
# 1. Choose test file or create new: test_<service>_whitebox.py
# 2. Create test class: TestNewFeature
# 3. Add test method: test_<scenario>_<expected>

class TestNewFeature:
    """Tests for new feature"""
    
    def test_scenario_returns_expected_result(self):
        """Descriptive test name"""
        # Arrange
        input_data = {...}
        
        # Act
        result = feature.process(input_data)
        
        # Assert
        assert result is not None
        assert result == expected_value
```

### Adding Black Box Test

```python
# 1. Choose test file or create new: test_<service>_blackbox.py
# 2. Create test class: TestNewEndpoint
# 3. Add test method: test_<scenario>_<expected>

class TestNewEndpoint:
    """Tests for new endpoint"""
    
    def test_endpoint_with_valid_data(self, api_client):
        """Test endpoint with valid input"""
        response = api_client.post(
            "service",
            "/endpoint",
            json={"data": "value"}
        )
        
        assert response.status_code == 200
        assert "result" in response.json()
```

---

## Resources

### Files to Read

1. **Start Here:**
   - `TESTING_SUMMARY.md` - Black box overview
   - `WHITEBOX_TESTING_SUMMARY.md` - White box overview

2. **For Details:**
   - `tests/README.md` - Black box detailed guide
   - `tests/WHITEBOX_README.md` - White box detailed guide
   - `TESTING_COMPARISON.md` - When to use each

3. **For References:**
   - `TESTING_QUICK_REFERENCE.md` - Quick commands
   - This file - Complete reference

### External Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Testing Best Practices](https://testingpython.com/)

---

## Quick Cheat Sheet

```bash
# Install
pip install -r tests/requirements_test.txt

# Run everything (just white box, no services needed)
pytest tests/test_*_whitebox.py -v

# Run with coverage
pytest tests/test_*_whitebox.py --cov=src --cov-report=html

# Run specific service
pytest tests/test_auth_service_whitebox.py -v

# Run specific test class
pytest tests/test_auth_service_whitebox.py::TestPasswordHashingLogic -v

# Run specific test
pytest tests/test_auth_service_whitebox.py::TestPasswordHashingLogic::test_verify_password_returns_true_for_matching -v

# Show slowest tests
pytest tests/ --durations=10

# Debug mode
pytest tests/test_auth_service_whitebox.py --pdb -v

# Parallel execution
pytest tests/ -n auto

# Stop on first failure
pytest tests/ -x
```

---

## Summary

### What You Have

✅ **295 Test Cases** (110 Black Box + 185 White Box)  
✅ **Comprehensive Documentation** (6 guides)  
✅ **Quick Scripts** (Windows + Linux)  
✅ **CI/CD Ready** (GitHub Actions, GitLab examples)  
✅ **High Quality** (Testing best practices implemented)  

### What to Do Now

1. Run white box tests: `pytest tests/test_*_whitebox.py -v`
2. Generate coverage: `pytest --cov=src tests/test_*_whitebox.py`
3. Read guides as needed
4. Add tests for new features
5. Configure CI/CD pipeline

### Expected Results

All tests should pass, coverage should be 80%+, and you'll have confidence in your code quality!

---

**Happy Testing!** 🚀
