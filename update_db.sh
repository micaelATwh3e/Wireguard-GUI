#!/bin/bash
# Update script for existing installations
# Applies all database migrations safely

set -e

echo "========================================"
echo "WireGuard VPN GUI - Database Update"
echo "========================================"
echo ""
echo "This script will update your database with:"
echo "  • Device management support"
echo "  • Allowed source IP restrictions"
echo "  • Other schema improvements"
echo ""
echo "✓ Safe to run on existing installations"
echo "✓ Skips already-applied migrations"
echo "✓ Backs up your database first"
echo ""

# Check if database exists
if [ ! -f "instance/vpn_gui.db" ]; then
    echo "❌ No database found at instance/vpn_gui.db"
    echo "   Run 'python init_db.py' to create a new database"
    exit 1
fi

echo "Database found: instance/vpn_gui.db"
echo ""

# Create backup
BACKUP_FILE="instance/vpn_gui.db.backup.$(date +%Y%m%d_%H%M%S)"
echo "Creating backup: $BACKUP_FILE"
cp instance/vpn_gui.db "$BACKUP_FILE"
echo "✓ Backup created"
echo ""

# Activate venv if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "⚠️  No virtual environment found"
    echo "   Using system Python"
fi

echo ""
echo "========================================"
echo "Running Database Migrations"
echo "========================================"
python3 migrate_db.py

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "✅ UPDATE SUCCESSFUL!"
    echo "========================================"
    echo ""
    echo "Your database has been updated to the latest schema."
    echo ""
    echo "Backup saved at:"
    echo "  $BACKUP_FILE"
    echo ""
    echo "To restore the backup if needed:"
    echo "  cp $BACKUP_FILE instance/vpn_gui.db"
    echo ""
    echo "NEXT STEPS:"
    echo "  1. Restart the application if it's running"
    echo "  2. Test the new features:"
    echo "     • Set allowed IPs when creating/editing users"
    echo "     • Manage multiple devices per user"
    echo ""
else
    echo ""
    echo "========================================"
    echo "❌ UPDATE FAILED"
    echo "========================================"
    echo ""
    echo "The migration encountered errors."
    echo "Your original database is safe."
    echo ""
    echo "To restore the backup:"
    echo "  cp $BACKUP_FILE instance/vpn_gui.db"
    echo ""
    echo "Please review the error messages above."
    exit 1
fi
