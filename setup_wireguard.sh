#!/bin/bash

# WireGuard Server Setup Script
# This script sets up WireGuard on a Linux server

set -e

echo "==================================="
echo "WireGuard Server Setup"
echo "==================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Install WireGuard
echo "Installing WireGuard..."
if command -v apt-get &> /dev/null; then
    apt-get update
    apt-get install -y wireguard wireguard-tools
elif command -v yum &> /dev/null; then
    yum install -y epel-release
    yum install -y wireguard-tools
else
    echo "Unsupported package manager. Please install WireGuard manually."
    exit 1
fi

echo "WireGuard installed successfully!"
echo ""

# Enable IP forwarding
echo "Enabling IP forwarding..."
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
echo "net.ipv6.conf.all.forwarding=1" >> /etc/sysctl.conf
sysctl -p

echo ""
echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and configure your settings"
echo "2. Update WG_SERVER_PUBLIC_IP in .env with your server's public IP"
echo "3. Run: python init_db.py"
echo "4. Run: sudo python app.py"
echo ""
echo "The web interface will be available at http://YOUR_SERVER_IP:5000"
echo ""
