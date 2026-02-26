# Allowed Source IPs Feature

## Overview
The VPN GUI now supports restricting which source IP addresses can connect to the VPN for each user. This is a security feature that adds an additional layer of protection by only allowing connections from trusted locations.

## How It Works

### Setting Allowed IPs for a User

1. **During User Creation:**
   - Navigate to Admin Dashboard → "Create New User"
   - Fill in the standard user information
   - In the "Allowed Source IPs" field, enter comma-separated IP addresses or CIDR ranges
   - Leave empty to allow connections from any IP address

2. **Editing Existing Users:**
   - Navigate to Admin Dashboard → Edit user
   - Update the "Allowed Source IPs" field
   - Changes take effect immediately after saving

### Format Examples

The system accepts various IP formats:

- **Single IPv4:** `203.0.113.50`
- **IPv4 CIDR:** `203.0.113.0/24`
- **Single IPv6:** `2001:db8::1`
- **IPv6 CIDR:** `2001:db8::/32`
- **Multiple IPs:** `203.0.113.0/24, 198.51.100.50, 2001:db8::/32`
- **Empty:** Leave blank to allow all IPs

### Validation

The system automatically validates all IP addresses and CIDR ranges when:
- Creating a new user
- Editing an existing user

If invalid IPs are entered, you'll receive an error message indicating which IP is invalid.

## Database Schema

### Added Field
- **Table:** `users`
- **Column:** `allowed_source_ips`
- **Type:** TEXT
- **Description:** Comma-separated list of IP addresses/CIDR ranges allowed to connect (NULL or empty = allow all)

## Migration

To apply this feature to an existing database:

```bash
cd /home/iwery/vpn_gui
source venv/bin/activate
python migrate_add_allowed_ips.py
```

## Security Considerations

1. **Empty Field = Allow All:** If the field is empty or NULL, the user can connect from any IP address
2. **CIDR Ranges:** Use CIDR notation to allow entire subnets (e.g., `192.168.1.0/24`)
3. **IPv6 Support:** Both IPv4 and IPv6 addresses are supported
4. **Immediate Effect:** Changes take effect once the WireGuard configuration is reloaded

## Use Cases

- **Home Office Users:** Restrict access to home IP address only
- **Corporate Networks:** Allow only corporate network ranges
- **Mobile Workers:** Use CIDR ranges for known mobile carrier IP blocks
- **High Security:** Combine with max_connections=1 for single device, single location access

## Technical Implementation

### Files Modified
1. `models.py` - Added `allowed_source_ips` field to User model
2. `app.py` - Added IP validation and form handling
3. `templates/add_user.html` - Added input field
4. `templates/edit_user.html` - Added input field
5. `migrate_add_allowed_ips.py` - Database migration script

### New Functions
- `validate_ip_list()` in `app.py` - Validates comma-separated IP addresses and CIDR ranges

## Future Enhancements

Potential improvements for this feature:
- Display allowed IPs in the admin dashboard table
- Add IP range presets (e.g., "Home", "Office")
- Show user's current IP address during editing for easy addition
- Log connection attempts from non-allowed IPs
- Support for IP whitelisting at the device level

## Notes

- This feature is stored in the database but enforcement depends on your WireGuard/firewall configuration
- For full enforcement, you may need to implement firewall rules based on these settings
- The IP validation uses Python's `ipaddress` module for RFC-compliant validation
