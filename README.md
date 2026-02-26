# WireGuard Web GUI [![Hits](https://hits.sh/github.com/micaelATwh3e/Wireguard-GUI.svg)](https://hits.sh/github.com/micaelATwh3e/Wireguard-GUI/)

A web-based management interface for WireGuard VPN with user authentication and self-service configuration download.

## Features

- **Admin Panel**: Add, update, and manage WireGuard users
- **User Portal**: Users can login and download their configuration files
- **Multi-Device Support**: Each user can manage multiple devices with separate configs
- **Connection Limits**: Enforce maximum simultaneous connections per user
- **IP Access Control**: Restrict VPN access to specific source IP addresses
- **QR Code Generation**: Mobile-friendly QR codes for easy setup
- **Automatic IP Assignment**: Automatically assigns IPs from the VPN subnet
- **User Management**: Enable/disable users without removing them
- **Real-time Monitoring**: Track connection status and device activity

## Requirements

- Python 3.8+
- WireGuard installed on the server
- Root/sudo access for WireGuard management

## Installation

### Quick Start (New Installation)
```bash
# 1. Run automated installer
./complete_install.sh
```

### Manual Installation

1. Clone or copy this project to your server

2. Install dependencies:
```bash
./install.sh
# OR manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Configure your settings:
```bash
cp .env.example .env
nano .env
```

Update the following in `.env`:
- `SECRET_KEY`: Generate a random secret key
- `WG_SERVER_PUBLIC_IP`: Your server's public IP address
- `ADMIN_PASSWORD`: Change the default admin password

4. Initialize the database:
```bash
source venv/bin/activate
python init_db.py
```

### Updating Existing Installation

If you already have the VPN GUI installed:

```bash
# Run the update script
./update_db.sh
```

See [DATABASE_SETUP.md](DATABASE_SETUP.md) for detailed update instructions.

5. Set up WireGuard server (if not already done):
```bash
sudo ./setup_wireguard.sh
```

6. Run the application:
```bash
sudo python app.py
```

The application will be available at `http://localhost:5000`

## Usage

### Admin Access
- URL: `/admin/login`
- Default username: `admin`
- Password: As set in `.env`

From the admin panel you can:
- Add new users with connection limits and IP restrictions
- Set allowed source IPs for enhanced security
- Configure max simultaneous connections per user
- View all users and their configurations
- Enable/disable users
- Delete users
- Manage user devices

### User Access
- URL: `/login`
- Users login with their assigned username and password
- Add and manage multiple devices
- Download configuration file as `.conf`
- View QR code for mobile setup
- See connection status for each device

## Documentation

- [DEVICE_MANAGEMENT.md](DEVICE_MANAGEMENT.md) - Multi-device feature guide
- [ALLOWED_IPS_FEATURE.md](ALLOWED_IPS_FEATURE.md) - IP access control guide
- [DATABASE_SETUP.md](DATABASE_SETUP.md) - Database setup and migration guide
- [QUICK_START.md](QUICK_START.md) - Quick reference guide

## Security Notes

- Always change default passwords
- Use HTTPS in production (consider nginx reverse proxy with Let's Encrypt)
- Run the app as a systemd service
- Keep WireGuard and system packages updated

## License

MIT
