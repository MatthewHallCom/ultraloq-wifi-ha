#!/bin/bash
# Test runner script that automatically handles virtual environment

set -e  # Exit on any error

echo "🧪 Running Ultraloq Wifi integration tests..."

# Check if setup script exists and run it if venv doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Virtual environment not found. Running setup..."
    ./setup_test_env.sh
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ No .env file found. Please create one with your credentials:"
    echo "   ULTRALOQ_EMAIL=your-email@example.com"
    echo "   ULTRALOQ_PASSWORD=your-password"
    echo ""
    echo "You can copy from the example: cp .env.example .env"
    exit 1
fi

# Default to pytest if no argument provided
TEST_TYPE=${1:-pytest}

echo "🏃 Running tests..."

case $TEST_TYPE in
    "manual")
        echo "Running manual test script..."
        python tests/run_tests.py
        ;;
    "auth")
        echo "Running authentication tests only..."
        pytest tests/test_api_standalone.py -m auth -v
        ;;
    "devices")
        echo "Running device discovery tests only..."
        pytest tests/test_api_standalone.py -m devices -v
        ;;
    "locks")
        echo "Running lock control tests only..."
        pytest tests/test_api_standalone.py -m locks -v
        ;;
    "coverage")
        echo "Running tests with coverage..."
        pytest tests/test_api_standalone.py --cov=tests.api_standalone --cov-report=html -v
        echo "📊 Coverage report generated in htmlcov/"
        ;;
    "pytest"|*)
        echo "Running pytest suite..."
        pytest tests/test_api_standalone.py -v
        ;;
esac

echo ""
echo "✅ Tests completed!"
echo ""
echo "💡 Usage:"
echo "  ./run_tests.sh          # Run all tests (default)"
echo "  ./run_tests.sh auth     # Run authentication tests only"
echo "  ./run_tests.sh devices  # Run device discovery tests only"
echo "  ./run_tests.sh locks    # Run lock control tests only"
echo "  ./run_tests.sh manual   # Run manual test script"
echo "  ./run_tests.sh coverage # Run with coverage report"