#!/bin/bash
# Setup script for device management and connection monitoring

echo "======================================"
echo "WireGuard Device Management Setup"
echo "======================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER="${SUDO_USER:-$USER}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Working directory: $SCRIPT_DIR"
echo "Running as user: $ACTUAL_USER"
echo ""

# Check if database is initialized
if [ ! -f "$SCRIPT_DIR/instance/wireguard.db" ]; then
    echo "⚠️  Database not found!"
    echo "Please run 'python init_db.py' first"
    exit 1
fi

echo "[1/5] Checking database for Device table..."
# The init_db.py already creates the Device table, so we just verify
sudo -u $ACTUAL_USER python3 -c "
from app import app
from models import Device
with app.app_context():
    try:
        Device.query.first()
        print('  ✓ Device table exists')
    except:
        print('  ⚠️  Device table not found, creating...')
        from models import db
        db.create_all()
        print('  ✓ Device table created')
" || {
    echo "  ❌ Failed to verify Device table"
    exit 1
}

echo ""
echo "[2/5] Migrating any existing user configs to devices..."
sudo -u $ACTUAL_USER python3 "$SCRIPT_DIR/migrate_add_devices.py"

if [ $? -ne 0 ]; then
    echo "Migration encountered issues. Check the messages above."
    echo "You can continue if the error is about WireGuard not running."
fi

echo ""
echo "[3/5] Making connection monitor executable..."
chmod +x "$SCRIPT_DIR/connection_monitor.py"

echo ""
echo "[4/5] Installing connection monitor service..."
# Create service file with correct paths
cat > /etc/systemd/system/wireguard-monitor.service << EOF
[Unit]
Description=WireGuard Connection Monitor
After=network.target wg-quick@wg0.service

[Service]
Type=simple
User=root
WorkingDirectory=$SCRIPT_DIR
Environment="PYTHONPATH=$SCRIPT_DIR"
ExecStart=/usr/bin/python3 $SCRIPT_DIR/connection_monitor.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable wireguard-monitor.service
systemctl restart wireguard-monitor.service

echo ""
echo "[5/5] Checking service status..."
sleep 2
systemctl status wireguard-monitor.service --no-pager || true

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Device management features enabled:"
echo "  ✓ Device model and database ready"
echo "  ✓ Existing configs migrated to devices"
echo "  ✓ Connection monitor service running"
echo ""
echo "Users can now:"
echo "  • Add multiple devices (up to their max_connections limit)"
echo "  • Each device gets unique keys and IP"
echo "  • Real-time connection monitoring"
echo "  • Automatic enforcement of connection limits"
echo ""
echo "Service commands:"
echo "  sudo systemctl status wireguard-monitor   # Check status"
echo "  sudo systemctl stop wireguard-monitor     # Stop monitoring"
echo "  sudo systemctl start wireguard-monitor    # Start monitoring"
echo "  sudo journalctl -u wireguard-monitor -f   # View logs"
echo ""
