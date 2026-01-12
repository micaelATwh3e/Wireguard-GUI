import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or 'sqlite:///wireguard.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # WireGuard Configuration
    WG_INTERFACE = os.environ.get('WG_INTERFACE', 'wg0')
    WG_SERVER_IP = os.environ.get('WG_SERVER_IP', '10.8.0.1')
    WG_SERVER_PUBLIC_IP = os.environ.get('WG_SERVER_PUBLIC_IP')
    WG_SERVER_PORT = int(os.environ.get('WG_SERVER_PORT', 51820))
    WG_DNS = os.environ.get('WG_DNS', '1.1.1.1,8.8.8.8')
    WG_SUBNET = '10.8.0.0/24'
    WG_NETWORK_INTERFACE = os.environ.get('WG_NETWORK_INTERFACE', 'eth0')
    
    # Admin credentials
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')
