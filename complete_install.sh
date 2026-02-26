#!/bin/bash
# Complete installation script - runs everything in order

set -e

echo "========================================"
echo "WireGuard VPN GUI - Complete Setup"
echo "With Device Management & Connection Limits"
echo "========================================"
echo ""

# Check if running as root for later steps
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Don't run this entire script as root!"
    echo "It will prompt for sudo when needed."
    exit 1
fi

echo "This script will:"
echo "  1. Install Python dependencies"
echo "  2. Initialize the database with Device support"
echo "  3. Setup connection monitoring service"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

echo ""
echo "========================================="
echo "STEP 1: Installing Dependencies"
echo "========================================="
bash install.sh

echo ""
echo "========================================="
echo "STEP 2: Checking Configuration"
echo "========================================="
if [ ! -f .env ]; then
    echo "⚠️  No .env file found!"
    if [ -f .env.example ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo "✓ Created .env file"
        echo ""
        echo "⚠️  IMPORTANT: Edit .env and set your configuration!"
        echo "   nano .env"
        echo ""
        read -p "Press Enter when you've configured .env..."
    else
        echo "❌ No .env.example found. Please create .env manually."
        exit 1
    fi
else
    echo "✓ .env file exists"
fi

echo ""
echo "========================================="
echo "STEP 3: Initializing Database"
echo "========================================="
source venv/bin/activate
python3 init_db.py

echo ""
echo "========================================="
echo "STEP 4: Installing Connection Monitor"
echo "========================================="
echo "This requires root privileges..."
sudo ./setup_device_management.sh

echo ""
echo "========================================"
echo "INSTALLATION COMPLETE! 🎉"
echo "========================================"
echo ""
echo "Your WireGuard VPN GUI is ready!"
echo ""
echo "FEATURES ENABLED:"
echo "  ✅ Multi-device management per user"
echo "  ✅ Enforced connection limits (max_connections)"
echo "  ✅ Allowed source IP restrictions"
echo "  ✅ Real-time connection monitoring"
echo "  ✅ Unique keys per device"
echo "  ✅ Per-device enable/disable"
echo ""
echo "NEXT STEPS:"
echo ""
echo "1. Make sure WireGuard is installed and configured:"
echo "   sudo ./setup_wireguard.sh"
echo ""
echo "2. Start the application:"
echo "   sudo python3 app.py"
echo "   (Requires sudo for WireGuard management)"
echo ""
echo "3. Access the web interface:"
echo "   http://localhost:5000"
echo ""
echo "4. Login with admin credentials from .env"
echo "   Default: admin / change-this-password"
echo ""
echo "5. Add users with max_connections limit"
echo "   Users can then add devices up to their limit"
echo ""
echo "MONITORING:"
echo "  • Connection monitor runs in background"
echo "  • Check status: sudo systemctl status wireguard-monitor"
echo "  • View logs: sudo journalctl -u wireguard-monitor -f"
echo ""
echo "For more info, see:"
echo "  • README.md - General usage"
echo "  • DEVICE_MANAGEMENT.md - Device features"
echo "  • PRE_INSTALL_CHECK.md - Troubleshooting"
echo ""
