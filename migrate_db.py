#!/usr/bin/env python3
"""
Master database migration script
Runs all necessary migrations in order for existing installations
"""

from app import app
from models import db, User, Device, WireGuardConfig
from wireguard_manager import WireGuardManager
from sqlalchemy import text
import sys

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    with app.app_context():
        try:
            result = db.session.execute(text(
                f"SELECT COUNT(*) FROM pragma_table_info('{table_name}') WHERE name='{column_name}'"
            ))
            return result.scalar() > 0
        except Exception as e:
            print(f"Error checking column: {e}")
            return False

def check_table_exists(table_name):
    """Check if a table exists"""
    with app.app_context():
        try:
            result = db.session.execute(text(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            ))
            return result.scalar() is not None
        except Exception as e:
            print(f"Error checking table: {e}")
            return False

def migrate_add_devices():
    """Add Device table and migrate existing user configs"""
    print("\n" + "="*60)
    print("Migration: Add Device Management")
    print("="*60)
    
    with app.app_context():
        if check_table_exists('devices'):
            print("✓ Device table already exists")
            return True
        
        print("Creating Device table...")
        db.create_all()
        print("✓ Device table created")
        
        # Migrate existing user configs to devices
        print("\nMigrating existing user configs to devices...")
        users = User.query.filter(User.wg_public_key.isnot(None)).all()
        
        migrated = 0
        for user in users:
            # Check if user already has a device
            existing_device = Device.query.filter_by(user_id=user.id).first()
            if existing_device:
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
            migrated += 1
            print(f"  ✓ Migrated '{user.username}' → 'Primary Device'")
        
        if migrated > 0:
            db.session.commit()
            print(f"\n✓ Migrated {migrated} user config(s)")
        else:
            print("  No users to migrate")
        
        return True

def migrate_add_allowed_ips():
    """Add allowed_source_ips column to users table"""
    print("\n" + "="*60)
    print("Migration: Add Allowed Source IPs")
    print("="*60)
    
    with app.app_context():
        if check_column_exists('users', 'allowed_source_ips'):
            print("✓ Column 'allowed_source_ips' already exists")
            return True
        
        print("Adding 'allowed_source_ips' column to users table...")
        db.session.execute(text(
            "ALTER TABLE users ADD COLUMN allowed_source_ips TEXT"
        ))
        db.session.commit()
        print("✓ Successfully added 'allowed_source_ips' column")
        
        return True

def run_migrations():
    """Run all migrations in order"""
    print("\n" + "="*60)
    print("Database Migration Suite")
    print("="*60)
    print("\nThis will update your database with the latest schema changes")
    print("Safe to run multiple times - skips already applied migrations\n")
    
    migrations = [
        ("Device Management", migrate_add_devices),
        ("Allowed Source IPs", migrate_add_allowed_ips),
    ]
    
    success_count = 0
    fail_count = 0
    
    for name, migration_func in migrations:
        try:
            if migration_func():
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"✗ Migration '{name}' failed: {e}")
            fail_count += 1
            db.session.rollback()
    
    print("\n" + "="*60)
    print("Migration Summary")
    print("="*60)
    print(f"✓ Successful: {success_count}")
    if fail_count > 0:
        print(f"✗ Failed: {fail_count}")
    
    if fail_count == 0:
        print("\n✅ All migrations completed successfully!")
        print("\nYour database is now up to date with:")
        print("  • Device management support")
        print("  • Allowed source IP restrictions")
        print("  • Connection limits per user")
        
        # Try to update WireGuard config
        print("\nAttempting to update WireGuard server configuration...")
        try:
            with app.app_context():
                WireGuardManager.apply_server_config()
            print("✓ WireGuard configuration updated")
        except Exception as e:
            print(f"⚠️  Could not update WireGuard config: {e}")
            print("   You may need to run with sudo privileges")
        
        return True
    else:
        print("\n⚠️  Some migrations failed. Please check the errors above.")
        return False

if __name__ == '__main__':
    try:
        result = run_migrations()
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        sys.exit(1)
