# Database Setup and Updates

## For New Installations

If you're setting up the VPN GUI for the first time:

```bash
# 1. Install dependencies
./install.sh

# 2. Configure settings
cp .env.example .env
nano .env

# 3. Initialize database
source venv/bin/activate
python init_db.py

# 4. Setup WireGuard and monitoring
sudo ./setup_wireguard.sh
sudo ./setup_device_management.sh

# 5. Start the application
sudo python app.py
```

## For Existing Installations

If you already have the VPN GUI running and want to update to the latest version:

### Quick Update (Recommended)

```bash
# Run the automated update script
./update_db.sh
```

This script will:
- ✓ Create an automatic backup of your database
- ✓ Apply all necessary migrations
- ✓ Preserve all your existing data
- ✓ Show clear success/failure messages

### Manual Update

If you prefer to run migrations manually:

```bash
# 1. Create a backup first!
cp instance/vpn_gui.db instance/vpn_gui.db.backup

# 2. Activate virtual environment
source venv/bin/activate

# 3. Run migrations
python migrate_db.py

# 4. Restart the application
sudo systemctl restart wireguard-gui  # if using systemd
# or
sudo pkill -f "python.*app.py" && sudo python app.py
```

## What Gets Updated

The migration scripts add the following improvements:

### Device Management
- ✓ Separate Device table for managing multiple devices per user
- ✓ Each device gets unique keys and IP address
- ✓ Per-device enable/disable controls
- ✓ Automatic migration of existing user configs

### Allowed Source IPs
- ✓ New `allowed_source_ips` field in User table
- ✓ Restrict VPN connections to specific IP addresses/ranges
- ✓ Support for IPv4 and IPv6 CIDR notation
- ✓ Empty = allow all IPs (backward compatible)

### Connection Monitoring
- ✓ Track device connection status in real-time
- ✓ Enforce max_connections limits per user
- ✓ Last handshake timestamps

## Migration Safety

All migration scripts are designed to be:
- **Idempotent**: Safe to run multiple times
- **Non-destructive**: Never deletes existing data
- **Backward compatible**: Old features continue to work

### Verification

After running migrations, verify everything worked:

```bash
# Check database structure
sqlite3 instance/vpn_gui.db ".schema users"
sqlite3 instance/vpn_gui.db ".schema devices"

# Should see:
# - users.allowed_source_ips (TEXT)
# - users.max_connections (INTEGER)
# - devices table exists
```

### Rollback

If you need to rollback (not recommended):

```bash
# Restore from backup
cp instance/vpn_gui.db.backup.YYYYMMDD_HHMMSS instance/vpn_gui.db

# Restart application
sudo systemctl restart wireguard-gui
```

## Individual Migration Scripts

You can also run individual migrations if needed:

### Add Device Management
```bash
python migrate_add_devices.py
```

### Add Allowed Source IPs
```bash
python migrate_add_allowed_ips.py
```

### Run All Migrations (Recommended)
```bash
python migrate_db.py
```

## Troubleshooting

### "No such column: allowed_source_ips"
Run the migration:
```bash
python migrate_db.py
```

### "No such table: devices"
Run the migration:
```bash
python migrate_db.py
```

### "Permission denied" errors
Some operations require root:
```bash
sudo -E venv/bin/python migrate_db.py
```

### Database locked
Stop the application first:
```bash
sudo systemctl stop wireguard-gui
sudo pkill -f "python.*app.py"
python migrate_db.py
sudo systemctl start wireguard-gui
```

## Database Location

Default database location:
```
instance/vpn_gui.db
```

Backups created by update_db.sh:
```
instance/vpn_gui.db.backup.YYYYMMDD_HHMMSS
```

## After Update

Once migrations are complete:

1. **Test the web interface** - Make sure you can log in
2. **Create a test user** - Try the new "Allowed Source IPs" field
3. **Add a device** - Users can now manage multiple devices
4. **Check monitoring** - Verify connection status updates

## Need Help?

- Check logs: `sudo journalctl -u wireguard-gui -f`
- Monitor service: `sudo journalctl -u wireguard-monitor -f`
- Review error messages from migration output
- Restore from backup if needed

## Version History

- **v1.0**: Initial release with basic user management
- **v2.0**: Added device management per user
- **v2.1**: Added allowed source IP restrictions
