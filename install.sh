#!/bin/bash

# Installation script for WireGuard Web GUI

set -e

echo "==================================="
echo "WireGuard Web GUI Installation"
echo "==================================="
echo ""

# Check Python version
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
echo "Found Python $PYTHON_VERSION"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "==================================="
echo "Installation Complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Configure your settings:"
echo "   cp .env.example .env"
echo "   nano .env"
echo ""
echo "2. Install WireGuard (requires root):"
echo "   sudo ./setup_wireguard.sh"
echo ""
echo "3. Initialize the database with device management:"
echo "   python init_db.py"
echo ""
echo "4. Install connection monitoring service (requires root):"
echo "   sudo ./setup_device_management.sh"
echo ""
echo "5. Start the application (requires root for WireGuard management):"
echo "   sudo venv/bin/python app.py"
echo ""
echo "6. Access the web interface at:"
echo "   http://localhost:5000"
echo ""
echo "7. Login with admin credentials (from .env):"
echo "   Default: admin / change-this-password"
echo ""
echo "FEATURES:"
echo "  ✓ Multi-device management per user"
echo "  ✓ Enforced connection limits"
echo "  ✓ Real-time connection monitoring"
echo "  ✓ Unique keys per device"
echo ""
