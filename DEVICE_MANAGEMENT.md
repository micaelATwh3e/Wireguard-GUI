# WireGuard VPN GUI - Device Management Update

## What Changed?

This update implements **true connection limit enforcement** through a device management system. Previously, the `max_connections` setting was just a database field with no actual enforcement.

## Key Features

### 1. **Device Model**
- Each user can now have multiple devices (up to their `max_connections` limit)
- Each device gets unique keys and IP address
- Devices are tracked individually with connection status

### 2. **Real Enforcement**
- Users CANNOT create more devices than their limit allows
- Each device has its own WireGuard config with unique keys
- Connection monitoring tracks which devices are actually connected

### 3. **Connection Monitoring**
- Background service (`connection_monitor.py`) monitors WireGuard handshakes
- Updates device connection status every 30 seconds
- Shows real-time which devices are connected

### 4. **User Interface**
- **Device Management Page**: Add, view, and manage multiple devices
- **Per-Device Actions**: Download config, show QR code, enable/disable, delete
- **Connection Status**: See which devices are currently connected
- **Device Limit Enforcement**: Clear indicators when limit is reached

## Installation

Run the setup script as root:

```bash
sudo ./setup_device_management.sh
```

This will:
1. Create the Device table in the database
2. Migrate existing user configs to devices (as "Primary Device")
3. Install and start the connection monitor service
4. Update WireGuard server configuration

## How It Works

### Before (Old System):
```
User → One Config → Shared across unlimited devices
         ↓
    max_connections field (not enforced)
```

### After (New System):
```
User → max_connections limit (enforced)
   ↓
   Device 1 → Unique keys + IP + Config
   Device 2 → Unique keys + IP + Config
   Device 3 → Unique keys + IP + Config
   ...
   (Cannot exceed max_connections)
```

### Connection Monitoring:
```
WireGuard handshakes → Connection Monitor Service → Database
                                                      ↓
                                            Device.is_connected
                                            Device.last_handshake
```

## Architecture

### New Files:
- `migrate_add_devices.py` - Database migration script
- `connection_monitor.py` - Background monitoring service
- `wireguard-monitor.service` - Systemd service definition
- `setup_device_management.sh` - Installation script
- `templates/manage_devices.html` - Device management UI
- `templates/add_device.html` - Add device form

### Updated Files:
- `models.py` - Added Device model
- `wireguard_manager.py` - Added device-specific methods
- `app.py` - Added device management routes
- `templates/user_dashboard.html` - Link to device management

## Usage

### For Users:
1. Go to "Manage Devices" from the dashboard
2. Click "Add Device" and enter a name (e.g., "iPhone", "Laptop")
3. Download the config or scan QR code
4. Repeat for each device (up to your limit)

### For Admins:
- Set `max_connections` when creating/editing users
- View all devices in the admin panel
- Monitor connection statistics

## Technical Details

### Device Limits Are Enforced At:
1. **Device Creation** - Cannot create more than `max_connections` devices
2. **Active Device Count** - Only active devices count toward limit
3. **Per-User Isolation** - Each user has their own device pool

### Connection Status:
- Handshake within 3 minutes = Connected
- No recent handshake = Disconnected
- Updated every 30 seconds by monitor service

### Backward Compatibility:
- Existing user configs are migrated as "Primary Device"
- Legacy configs still work (shown as "Legacy Config" in stats)
- Old download/QR code routes still functional

## Service Management

```bash
# Check monitor status
sudo systemctl status wireguard-monitor

# View logs
sudo journalctl -u wireguard-monitor -f

# Restart monitor
sudo systemctl restart wireguard-monitor

# Stop monitor
sudo systemctl stop wireguard-monitor
```

## Benefits

✅ **Actually enforces** connection limits
✅ Each device has unique keys (better security)
✅ Track which devices are connected
✅ Revoke access per-device (not all-or-nothing)
✅ Real-time connection monitoring
✅ Clear UI for managing multiple devices
✅ Backward compatible with existing configs

## Example Scenario

**User "alice" with max_connections=3:**

1. Adds "iPhone" → Gets unique config
2. Adds "Laptop" → Gets different config
3. Adds "iPad" → Gets third config
4. Tries to add "Desktop" → **BLOCKED** (limit reached)
5. Deletes "iPad" → Can now add "Desktop"

**Connection Monitor:**
- iPhone connects → Shows as "Connected"
- Laptop disconnects → Shows as "Disconnected"
- Real-time status visible in UI
