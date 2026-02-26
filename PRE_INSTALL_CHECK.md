# Pre-Installation Checklist

## Will Everything Work? YES! ✅

Here's what will happen during installation:

## Database Design

### ✅ Existing Tables (Already There)
```sql
users
  - id, username, password_hash, email
  - is_admin, is_active, created_at
  - wg_public_key, wg_private_key, wg_preshared_key  (kept for backward compatibility)
  - wg_ip_address, wg_allowed_ips
  - max_connections  (now actually enforced!)

wireguard_config
  - id, server_private_key, server_public_key
  - last_ip_assigned
```

### ✅ New Table (Will Be Created)
```sql
devices
  - id, user_id (FK to users)
  - device_name
  - wg_public_key, wg_private_key, wg_preshared_key  (unique per device)
  - wg_ip_address (unique per device)
  - wg_allowed_ips
  - is_active, is_connected
  - created_at, last_handshake
```

## Installation Process

### Step 1: Migration Script
```bash
python3 migrate_add_devices.py
```

**What it does:**
1. Creates the `devices` table
2. Migrates existing user configs → becomes "Primary Device"
3. Preserves all existing data
4. Updates WireGuard server config

**Safe:** Your existing users and configs are NOT deleted, just copied to devices table.

### Step 2: Connection Monitor Service
```bash
systemctl start wireguard-monitor
```

**What it does:**
1. Runs in background every 30 seconds
2. Checks WireGuard handshakes
3. Updates `devices.is_connected` status
4. Logs to `/var/log/wireguard-monitor.log`

## Full Functionality ✅

After installation, you'll have:

### User Features
- ✅ View all their devices
- ✅ Add new devices (enforced limit!)
- ✅ Download configs per device
- ✅ Generate QR codes per device
- ✅ See which devices are connected
- ✅ Enable/disable devices
- ✅ Delete devices

### Admin Features
- ✅ Set max_connections per user
- ✅ View all devices across all users
- ✅ See connection statistics
- ✅ Monitor real-time connections

### Enforcement
- ✅ Cannot create more than max_connections devices
- ✅ Each device has unique keys (can't copy configs)
- ✅ Real-time connection tracking
- ✅ Per-device management

## Dependencies

All required packages are in `requirements.txt`:
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Werkzeug==3.0.1
qrcode==7.4.2
Pillow>=10.3.0
python-dotenv==1.0.0
```

No new dependencies needed! ✅

## Backward Compatibility

### Existing Users
- ✅ Old configs still work
- ✅ Automatically migrated to "Primary Device"
- ✅ Can add more devices if they have max_connections > 1

### Legacy Routes
- ✅ `/download-config` still works (uses legacy config or first device)
- ✅ `/qr-code` still works
- ✅ Old admin functions unchanged

## Test Before Installing

Run the test script to verify everything:

```bash
python3 test_device_system.py
```

This will:
1. Check database schema
2. Test device creation with limits
3. Test connection monitoring
4. Test config generation

## Installation Command

Once tests pass:

```bash
sudo ./setup_device_management.sh
```

## What Could Go Wrong?

### Issue 1: WireGuard Not Running
**Error:** "Cannot connect to WireGuard"
**Fix:** Make sure WireGuard is running: `sudo wg-quick up wg0`

### Issue 2: Permission Denied
**Error:** "Permission denied" when updating config
**Fix:** Run with sudo: `sudo ./setup_device_management.sh`

### Issue 3: Port Already in Use
**Error:** Service won't start
**Fix:** Check if old service is running: `ps aux | grep python`

## Rollback Plan

If something goes wrong:

```bash
# Stop monitor service
sudo systemctl stop wireguard-monitor

# Disable monitor service
sudo systemctl disable wireguard-monitor

# Old system still works with User.wg_* fields
# Just use legacy download route
```

Your original data is safe! The Device table is separate.

## Ready to Install?

1. ✅ Test: `python3 test_device_system.py`
2. ✅ Backup: `cp instance/vpn.db instance/vpn.db.backup`
3. ✅ Install: `sudo ./setup_device_management.sh`
4. ✅ Test: Login and try adding a device!

## Expected Result

After successful installation:

```
✅ Device table created
✅ Existing configs migrated
✅ Monitor service running
✅ New routes available:
   - /devices
   - /devices/add
   - /devices/<id>/download
   - /devices/<id>/qr-code
   - /devices/<id>/toggle
   - /devices/<id>/delete
✅ Templates loaded
✅ Real-time monitoring active
```

**Your system will have FULL device management with enforced limits!** 🎉
