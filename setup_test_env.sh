#!/bin/bash
# Setup script for Ultraloq Wifi integration testing environment

set -e  # Exit on any error

echo "🔧 Setting up Ultraloq Wifi test environment..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found. Please install Python 3."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "📦 Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install test requirements
echo "📥 Installing test dependencies..."
pip install -r requirements-test.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️ No .env file found. Creating from example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your Ultraloq credentials:"
    echo "   - ULTRALOQ_EMAIL=your-email@example.com"
    echo "   - ULTRALOQ_PASSWORD=your-password"
    echo ""
    echo "Then run: ./run_tests.sh"
else
    echo "✅ .env file exists"
fi

echo ""
echo "🎉 Test environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials (if not done already)"
echo "2. Run tests: ./run_tests.sh"
echo "3. Or activate environment manually: source venv/bin/activate"