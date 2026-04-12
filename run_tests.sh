#!/bin/bash
# Script to run black box tests with various options

echo ""
echo "========================================"
echo "Log-Driven Incident Response"
echo "Black Box Testing Suite"
echo "========================================"
echo ""

# Check if pytest is installed
if ! python -m pytest --version &> /dev/null; then
    echo "ERROR: pytest is not installed"
    echo "Please install dependencies: pip install -r tests/requirements_test.txt"
    exit 1
fi

# Parse command line arguments
case "${1:-}" in
    "")
        echo "Usage: ./run_tests.sh [option]"
        echo ""
        echo "Options:"
        echo "  all              Run all tests"
        echo "  auth             Run auth service tests"
        echo "  incident         Run incident management tests"
        echo "  detection        Run detection service tests"
        echo "  ingestion        Run log ingestion tests"
        echo "  coverage         Run tests with coverage report"
        echo "  verbose          Run all tests with verbose output"
        echo "  parallel         Run tests in parallel"
        echo "  report           Generate HTML test report"
        echo ""
        exit 0
        ;;
    
    "all")
        echo "Running all tests..."
        python -m pytest tests/ -v
        ;;
    
    "auth")
        echo "Running auth service tests..."
        python -m pytest tests/test_auth_service_blackbox.py -v
        ;;
    
    "incident")
        echo "Running incident management tests..."
        python -m pytest tests/test_incident_management_blackbox.py -v
        ;;
    
    "detection")
        echo "Running detection service tests..."
        python -m pytest tests/test_detection_service_blackbox.py -v
        ;;
    
    "ingestion")
        echo "Running log ingestion tests..."
        python -m pytest tests/test_log_ingestion_blackbox.py -v
        ;;
    
    "coverage")
        echo "Running tests with coverage report..."
        python -m pytest tests/ --cov=src --cov-report=html --cov-report=term
        echo ""
        echo "Coverage report generated in htmlcov/index.html"
        ;;
    
    "verbose")
        echo "Running all tests with verbose output..."
        python -m pytest tests/ -vv
        ;;
    
    "parallel")
        echo ""
        echo "Note: Install pytest-xdist for parallel testing"
        echo "  pip install pytest-xdist"
        echo ""
        python -m pytest tests/ -n auto -v
        ;;
    
    "report")
        echo ""
        echo "Note: Install pytest-html for HTML reports"
        echo "  pip install pytest-html"
        echo ""
        python -m pytest tests/ -v --html=tests_report.html --self-contained-html
        echo ""
        echo "Test report generated in tests_report.html"
        ;;
    
    *)
        echo "Unknown option: $1"
        echo "Run './run_tests.sh' without arguments for usage information"
        exit 1
        ;;
esac

echo ""
echo "Test run completed!"
exit 0
