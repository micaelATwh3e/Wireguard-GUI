from models import db, User, WireGuardConfig
from config import Config
from flask import Flask
import subprocess
import os

def init_database():
    """Initialize the database and create admin user"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if admin exists
        admin = User.query.filter_by(username=Config.ADMIN_USERNAME).first()
        if not admin:
            admin = User(
                username=Config.ADMIN_USERNAME,
                email='admin@localhost',
                is_admin=True
            )
            admin.set_password(Config.ADMIN_PASSWORD)
            db.session.add(admin)
            print(f"Admin user created: {Config.ADMIN_USERNAME}")
        
        # Initialize WireGuard config if not exists
        wg_config = WireGuardConfig.query.first()
        if not wg_config:
            # Generate server keys
            try:
                private_key = subprocess.check_output(['wg', 'genkey']).decode().strip()
                public_key = subprocess.check_output(
                    ['wg', 'pubkey'], 
                    input=private_key.encode()
                ).decode().strip()
                
                wg_config = WireGuardConfig(
                    server_private_key=private_key,
                    server_public_key=public_key,
                    last_ip_assigned=1
                )
                db.session.add(wg_config)
                print("WireGuard server keys generated")
            except Exception as e:
                print(f"Warning: Could not generate WireGuard keys: {e}")
                print("Make sure WireGuard is installed: sudo apt install wireguard")
        
        db.session.commit()
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_database()
