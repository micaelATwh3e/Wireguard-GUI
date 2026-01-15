# Quick Start Guide

## Fresh Installation (New System)

For a brand new installation with device management:

```bash
# 1. Run complete installation
./complete_install.sh

# 2. That's it! The script handles everything.
```

The complete installer will:
- Install Python dependencies
- Initialize database with Device table
- Setup connection monitoring service
- Configure everything automatically

## Manual Installation (Step by Step)

If you prefer to run each step manually:

### Step 1: Install Dependencies
```bash
bash install.sh
```

### Step 2: Configure Environment
```bash
cp .env.example .env
nano .env  # Edit your settings
```

### Step 3: Initialize Database (Now includes Device table!)
```bash
python3 init_db.py
```

This creates:
- ✅ User table
- ✅ WireGuardConfig table  
- ✅ **Device table** (new!)

### Step 4: Setup Connection Monitoring
```bash
sudo ./setup_device_management.sh
```

This:
- Migrates existing user configs to devices
- Installs background monitoring service
- Starts connection tracking

### Step 5: Start Application
```bash
sudo python3 app.py
```

## Upgrading Existing Installation

If you already have the VPN GUI installed:

```bash
# 1. Backup your database
cp instance/wireguard.db instance/wireguard.db.backup

# 2. Update code (pull latest changes)
git pull

# 3. Install new dependencies (if any)
pip install -r requirements.txt

# 4. Run migration
python3 migrate_add_devices.py

# 5. Setup monitoring service
sudo ./setup_device_management.sh

# 6. Restart application
sudo systemctl restart wireguard-gui  # or restart manually
```

## Verification

Check everything is working:

```bash
# Verify installation is ready
python3 verify_ready.py

# Should show all checks passed
```

## First Login

1. Open browser: `http://localhost:5000`
2. Login with admin credentials (from `.env`)
3. Add a user with `max_connections > 1`
4. Login as that user
5. Click "Manage Devices"
6. Add your first device!

## Testing Device Limits

Try this to verify limits work:

1. Create user with `max_connections = 2`
2. User adds "Device 1" - ✅ Success
3. User adds "Device 2" - ✅ Success  
4. User tries "Device 3" - ❌ **BLOCKED!**
5. User deletes "Device 1"
6. User adds "Device 3" - ✅ Success (now has slot)

## What Changed?

### Before (Old System):
- One config per user
- Could be copied to unlimited devices
- `max_connections` was just a number (not enforced)

### After (New System):
- Multiple configs per user (one per device)
- Each device has unique keys
- Cannot create more devices than `max_connections` limit
- Real-time tracking of which devices are connected

## Troubleshooting

### "Device table not found"
Run: `python3 init_db.py` (it now creates Device table automatically)

### "Monitor service won't start"
Check: `sudo journalctl -u wireguard-monitor -f`

### "WireGuard not installed"
Run: `sudo apt install wireguard` (or `sudo ./setup_wireguard.sh`)

### "Permission denied"
Most WireGuard operations need root: `sudo python3 app.py`

## Quick Reference

```bash
# Check everything is ready
python3 verify_ready.py

# Initialize fresh database
python3 init_db.py

# Migrate existing users
python3 migrate_add_devices.py

# Setup monitoring
sudo ./setup_device_management.sh

# Check monitor status
sudo systemctl status wireguard-monitor

# View monitor logs
sudo journalctl -u wireguard-monitor -f

# Restart monitor
sudo systemctl restart wireguard-monitor
```

## Features You Get

✅ **Device Management**
- Users can add multiple devices
- Each device has unique keys and IP
- Download config or scan QR per device

✅ **Enforced Limits**
- Cannot exceed `max_connections`
- Blocked at device creation time
- Clear error messages

✅ **Real-Time Monitoring**
- Shows which devices are connected
- Updates every 30 seconds
- Last seen timestamps

✅ **Per-Device Control**
- Enable/disable individual devices
- Delete devices
- View connection history

## Support

- Full docs: `DEVICE_MANAGEMENT.md`
- Pre-install check: `PRE_INSTALL_CHECK.md`
- General usage: `README.md`
