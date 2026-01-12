# WireGuard Web GUI

A web-based management interface for WireGuard VPN with user authentication and self-service configuration download.

## Features

- **Admin Panel**: Add, update, and manage WireGuard users
- **User Portal**: Users can login and download their configuration files
- **QR Code Generation**: Mobile-friendly QR codes for easy setup
- **Automatic IP Assignment**: Automatically assigns IPs from the VPN subnet
- **User Management**: Enable/disable users without removing them

## Requirements

- Python 3.8+
- WireGuard installed on the server
- Root/sudo access for WireGuard management

## Installation

1. Clone or copy this project to your server

2. Install dependencies:
```bash
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
python init_db.py
```

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
- Add new users
- View all users and their configurations
- Enable/disable users
- Delete users

### User Access
- URL: `/login`
- Users login with their assigned username and password
- Download configuration file as `.conf`
- View QR code for mobile setup

## Security Notes

- Always change default passwords
- Use HTTPS in production (consider nginx reverse proxy with Let's Encrypt)
- Run the app as a systemd service
- Keep WireGuard and system packages updated

## License

MIT
