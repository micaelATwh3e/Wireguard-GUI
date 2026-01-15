from models import db, User, WireGuardConfig, Device
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
        # Create all tables (including Device table)
        print("Creating database tables...")
        db.create_all()
        print("✓ All tables created (User, WireGuardConfig, Device)")
        
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
            print(f"✓ Admin user created: {Config.ADMIN_USERNAME}")
        else:
            print(f"✓ Admin user already exists: {Config.ADMIN_USERNAME}")
        
        # Initialize WireGuard config if not exists
        wg_config = WireGuardConfig.query.first()
        if not wg_config:
            # Generate server keys
            try:
                wg_cmd = '/usr/bin/wg'
                private_key = subprocess.check_output([wg_cmd, 'genkey']).decode().strip()
                public_key = subprocess.check_output(
                    [wg_cmd, 'pubkey'], 
                    input=private_key.encode()
                ).decode().strip()
                
                wg_config = WireGuardConfig(
                    server_private_key=private_key,
                    server_public_key=public_key,
                    last_ip_assigned=1
                )
                db.session.add(wg_config)
                print("✓ WireGuard server keys generated")
                print(f"  Server public key: {public_key[:32]}...")
            except Exception as e:
                print(f"⚠️  Warning: Could not generate WireGuard keys: {e}")
                print("   Make sure WireGuard is installed: sudo apt install wireguard")
        else:
            print("✓ WireGuard configuration already exists")
        
        db.session.commit()
        
        print("\n" + "="*60)
        print("DATABASE INITIALIZED SUCCESSFULLY!")
        print("="*60)
        print("\n✅ Ready for device management system")
        print("   - User table: ✓")
        print("   - Device table: ✓")
        print("   - WireGuardConfig table: ✓")
        print("\nYou can now:")
        print("   • Add users with max_connections limit")
        print("   • Users can manage multiple devices")
        print("   • Each device gets unique keys and IP")
        print("   • Connection limits are enforced")

if __name__ == '__main__':
    init_database()
