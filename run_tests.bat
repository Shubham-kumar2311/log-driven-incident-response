@echo off
REM Script to run black box tests with various options

echo.
echo ========================================
echo Log-Driven Incident Response
echo Black Box Testing Suite
echo ========================================
echo.

REM Check if pytest is installed
python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pytest is not installed
    echo Please install dependencies: pip install -r tests/requirements_test.txt
    exit /b 1
)

REM Parse command line arguments
if "%1"=="" (
    echo Usage: run_tests.bat [option]
    echo.
    echo Options:
    echo   all              Run all tests
    echo   auth             Run auth service tests
    echo   incident         Run incident management tests
    echo   detection        Run detection service tests
    echo   ingestion        Run log ingestion tests
    echo   coverage         Run tests with coverage report
    echo   verbose          Run all tests with verbose output
    echo   parallel         Run tests in parallel
    echo   report           Generate HTML test report
    echo.
    exit /b 0
)

if "%1"=="all" (
    echo Running all tests...
    python -m pytest tests/ -v
    goto :end
)

if "%1"=="auth" (
    echo Running auth service tests...
    python -m pytest tests/test_auth_service_blackbox.py -v
    goto :end
)

if "%1"=="incident" (
    echo Running incident management tests...
    python -m pytest tests/test_incident_management_blackbox.py -v
    goto :end
)

if "%1"=="detection" (
    echo Running detection service tests...
    python -m pytest tests/test_detection_service_blackbox.py -v
    goto :end
)

if "%1"=="ingestion" (
    echo Running log ingestion tests...
    python -m pytest tests/test_log_ingestion_blackbox.py -v
    goto :end
)

if "%1"=="coverage" (
    echo Running tests with coverage report...
    python -m pytest tests/ --cov=src --cov-report=html --cov-report=term
    echo.
    echo Coverage report generated in htmlcov/index.html
    goto :end
)

if "%1"=="verbose" (
    echo Running all tests with verbose output...
    python -m pytest tests/ -vv
    goto :end
)

if "%1"=="parallel" (
    echo.
    echo Note: Install pytest-xdist for parallel testing
    echo   pip install pytest-xdist
    echo.
    python -m pytest tests/ -n auto -v
    goto :end
)

if "%1"=="report" (
    echo.
    echo Note: Install pytest-html for HTML reports
    echo   pip install pytest-html
    echo.
    python -m pytest tests/ -v --html=tests_report.html --self-contained-html
    echo.
    echo Test report generated in tests_report.html
    goto :end
)

echo Unknown option: %1
echo Run 'run_tests.bat' without arguments for usage information
exit /b 1

:end
echo.
echo Test run completed!
exit /b 0
