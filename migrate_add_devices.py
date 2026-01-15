"""
Migration script to add Device table and migrate existing user configs
"""
from app import app
from models import db, User, Device
from wireguard_manager import WireGuardManager

def migrate():
    with app.app_context():
        print("Creating Device table...")
        db.create_all()
        
        print("\nMigrating existing user configs to devices...")
        users = User.query.filter(User.wg_public_key.isnot(None)).all()
        
        for user in users:
            # Check if user already has a device
            existing_device = Device.query.filter_by(user_id=user.id).first()
            if existing_device:
                print(f"  User '{user.username}' already has device(s), skipping...")
                continue
            
            # Create a device from existing user config
            device = Device(
                user_id=user.id,
                device_name="Primary Device",
                wg_public_key=user.wg_public_key,
                wg_private_key=user.wg_private_key,
                wg_preshared_key=user.wg_preshared_key,
                wg_ip_address=user.wg_ip_address,
                wg_allowed_ips=user.wg_allowed_ips or '0.0.0.0/0',
                is_active=user.is_active
            )
            
            db.session.add(device)
            print(f"  Migrated '{user.username}' config to device 'Primary Device'")
        
        db.session.commit()
        print("\nMigration completed!")
        print("\nUpdating WireGuard server configuration...")
        
        try:
            WireGuardManager.apply_server_config_with_devices()
            print("Server configuration updated successfully!")
        except Exception as e:
            print(f"Warning: Could not update server config: {e}")
            print("You may need to run this manually with sudo privileges")

if __name__ == '__main__':
    migrate()
