#!/usr/bin/env python3
"""
Pre-installation verification - checks if system is ready to install
"""
from app import app
from models import db, User, WireGuardConfig
import os

def check_database_exists():
    """Check if database file exists"""
    print("Checking database...")
    db_paths = ['instance/wireguard.db', 'instance/vpn.db', 'wireguard.db']
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"  ✓ Database exists: {db_path}")
            return True
    
    print(f"  ❌ Database not found")
    print(f"     Checked: {', '.join(db_paths)}")
    print(f"     Run: python3 init_db.py")
    return False

def check_wireguard_config():
    """Check if WireGuard is configured"""
    print("\nChecking WireGuard configuration...")
    with app.app_context():
        try:
            wg_config = WireGuardConfig.query.first()
            if wg_config:
                print(f"  ✓ WireGuard server configured")
                print(f"    Server public key: {wg_config.server_public_key[:16]}...")
                return True
            else:
                print(f"  ⚠️  WireGuard not configured yet")
                print(f"     Run: python3 init_db.py")
                return False
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False

def check_existing_users():
    """Check if there are existing users"""
    print("\nChecking existing users...")
    with app.app_context():
        try:
            users = User.query.all()
            if users:
                print(f"  ✓ Found {len(users)} existing user(s)")
                for user in users:
                    has_config = "✓ has config" if user.wg_public_key else "⚠️ no config"
                    print(f"    - {user.username}: {has_config}, max_connections={user.max_connections}")
                return True
            else:
                print(f"  ⚠️  No users found (system is empty)")
                return True  # Not an error
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False

def check_permissions():
    """Check file permissions"""
    print("\nChecking file permissions...")
    files_to_check = [
        'app.py',
        'models.py',
        'wireguard_manager.py',
        'migrate_add_devices.py',
        'connection_monitor.py',
        'setup_device_management.sh'
    ]
    
    all_ok = True
    for file in files_to_check:
        if os.path.exists(file):
            print(f"  ✓ {file} exists")
        else:
            print(f"  ❌ {file} missing!")
            all_ok = False
    
    return all_ok

def check_python_packages():
    """Check if required packages are installed"""
    print("\nChecking Python packages...")
    required = ['flask', 'flask_sqlalchemy', 'flask_login', 'qrcode']
    
    all_ok = True
    for package in required:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ❌ {package} not installed")
            all_ok = False
    
    if not all_ok:
        print("\n  Run: pip install -r requirements.txt")
    
    return all_ok

def main():
    print("="*60)
    print("PRE-INSTALLATION VERIFICATION")
    print("="*60)
    print()
    
    checks = [
        check_python_packages,
        check_permissions,
        check_database_exists,
        check_wireguard_config,
        check_existing_users
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Check failed: {e}")
            results.append(False)
    
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All checks passed ({passed}/{total})")
        print("\n" + "="*60)
        print("READY TO INSTALL!")
        print("="*60)
        print("\nNext steps:")
        print("1. Create a backup:")
        print("   cp instance/vpn.db instance/vpn.db.backup")
        print("\n2. Run the installation:")
        print("   sudo ./setup_device_management.sh")
        print("\n3. This will:")
        print("   ✓ Create Device table")
        print("   ✓ Migrate existing configs to devices")
        print("   ✓ Install connection monitor service")
        print("   ✓ Update WireGuard configuration")
        print()
    else:
        print(f"⚠️  {passed}/{total} checks passed")
        print("\nPlease fix the issues above before installing.")
        print("\nCommon fixes:")
        print("- Missing packages: pip install -r requirements.txt")
        print("- No database: python3 init_db.py")
        print("- Permission errors: chmod +x setup_device_management.sh")
    
    return passed == total

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
