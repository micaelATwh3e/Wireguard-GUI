#!/bin/bash
# Git commit helper - Use this to commit the device management changes

cd "$(dirname "$0")"

echo "================================================"
echo "Git Commit - Device Management System"
echo "================================================"
echo ""

# Show what will be committed
echo "Files staged for commit:"
git diff --cached --name-only

echo ""
echo "================================================"
echo "Suggested commit message:"
echo "================================================"
cat << 'EOF'

feat: Add multi-device management with enforced connection limits

This major update implements true device management and connection limit
enforcement:

Features:
- Multi-device support: Users can add multiple devices (up to max_connections)
- Unique keys per device: Each device gets its own WireGuard configuration
- Enforced limits: Cannot create more devices than allowed
- Real-time monitoring: Background service tracks which devices are connected
- Per-device management: Enable/disable/delete individual devices

New Components:
- Device model with relationship to User
- Device management UI (manage_devices.html, add_device.html)
- Connection monitoring service (connection_monitor.py)
- Migration script (migrate_add_devices.py)
- Updated routes and templates

Database Changes:
- New Device table with foreign key to User
- Tracks connection status and last handshake per device
- Backward compatible with existing User configs

Installation:
- Run: ./complete_install.sh (automated)
- Or: python init_db.py && sudo ./setup_device_management.sh

Documentation:
- QUICK_START.md: Installation guide
- DEVICE_MANAGEMENT.md: Feature documentation

Breaking Changes: None (backward compatible)

EOF

echo ""
echo "================================================"
echo ""
read -p "Ready to commit? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git commit -m "feat: Add multi-device management with enforced connection limits

This major update implements true device management and connection limit enforcement.

Features:
- Multi-device support per user (up to max_connections limit)
- Unique WireGuard keys and IP per device
- Enforced connection limits at device creation
- Real-time connection monitoring service
- Per-device enable/disable/delete controls

New Components:
- Device model with User relationship
- Device management UI templates
- Connection monitoring background service
- Migration script for existing configs
- Complete installation automation

See QUICK_START.md and DEVICE_MANAGEMENT.md for details."
    
    echo ""
    echo "✓ Committed!"
    echo ""
    echo "To push to remote:"
    echo "  git push origin main"
else
    echo "Commit cancelled. You can commit manually with:"
    echo "  git commit"
fi
