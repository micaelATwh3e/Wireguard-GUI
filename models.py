from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # WireGuard specific fields (legacy - kept for backward compatibility)
    wg_public_key = db.Column(db.String(255))
    wg_private_key = db.Column(db.String(255))
    wg_preshared_key = db.Column(db.String(255))
    wg_ip_address = db.Column(db.String(15))  # e.g., 10.8.0.2
    wg_allowed_ips = db.Column(db.String(255), default='0.0.0.0/0')
    max_connections = db.Column(db.Integer, default=1)  # Maximum simultaneous connections allowed
    
    # Relationship to devices
    devices = db.relationship('Device', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class WireGuardConfig(db.Model):
    __tablename__ = 'wireguard_config'
    
    id = db.Column(db.Integer, primary_key=True)
    server_private_key = db.Column(db.String(255), nullable=False)
    server_public_key = db.Column(db.String(255), nullable=False)
    last_ip_assigned = db.Column(db.Integer, default=1)  # Last octet of IP
    
    def __repr__(self):
        return f'<WireGuardConfig>'


class Device(db.Model):
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    device_name = db.Column(db.String(100), nullable=False)  # e.g., "iPhone", "Laptop"
    wg_public_key = db.Column(db.String(255), unique=True, nullable=False)
    wg_private_key = db.Column(db.String(255), nullable=False)
    wg_preshared_key = db.Column(db.String(255))
    wg_ip_address = db.Column(db.String(15), unique=True, nullable=False)  # e.g., 10.8.0.2
    wg_allowed_ips = db.Column(db.String(255), default='0.0.0.0/0')
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_handshake = db.Column(db.DateTime, nullable=True)  # Last successful connection
    is_connected = db.Column(db.Boolean, default=False)  # Currently connected
    
    def __repr__(self):
        return f'<Device {self.device_name} - {self.user.username}>'

