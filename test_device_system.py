#!/usr/bin/env python3
"""
Test script to verify device management system is working correctly
"""
from app import app
from models import db, User, Device, WireGuardConfig
from wireguard_manager import WireGuardManager

def test_database_schema():
    """Test that all tables and columns exist"""
    print("Testing database schema...")
    
    with app.app_context():
        try:
            # Test User table
            user_columns = User.__table__.columns.keys()
            required_user_cols = ['id', 'username', 'password_hash', 'max_connections']
            for col in required_user_cols:
                assert col in user_columns, f"Missing User column: {col}"
            print("  ✓ User table has all required columns")
            
            # Test Device table
            device_columns = Device.__table__.columns.keys()
            required_device_cols = ['id', 'user_id', 'device_name', 'wg_public_key', 
                                   'wg_private_key', 'wg_ip_address', 'is_active', 
                                   'is_connected', 'last_handshake']
            for col in required_device_cols:
                assert col in device_columns, f"Missing Device column: {col}"
            print("  ✓ Device table has all required columns")
            
            # Test relationships
            user = User.query.first()
            if user:
                devices = user.devices
                print(f"  ✓ User-Device relationship working (user has {len(devices)} devices)")
            
            print("✅ Database schema is correct!\n")
            return True
            
        except Exception as e:
            print(f"❌ Schema error: {e}\n")
            return False

def test_device_creation():
    """Test creating devices with limits"""
    print("Testing device creation and limits...")
    
    with app.app_context():
        try:
            # Find or create a test user
            test_user = User.query.filter_by(username='test_device_user').first()
            if not test_user:
                test_user = User(
                    username='test_device_user',
                    email='test@example.com',
                    max_connections=2
                )
                test_user.set_password('testpass')
                db.session.add(test_user)
                db.session.commit()
                print(f"  ✓ Created test user with max_connections=2")
            else:
                # Clean up old devices
                Device.query.filter_by(user_id=test_user.id).delete()
                db.session.commit()
                print(f"  ✓ Using existing test user (cleaned up old devices)")
            
            # Test 1: Create first device (should succeed)
            try:
                device1, config1 = WireGuardManager.create_device_config(test_user, "Test Device 1")
                print(f"  ✓ Created device 1: {device1.device_name} ({device1.wg_ip_address})")
            except Exception as e:
                print(f"  ❌ Failed to create device 1: {e}")
                return False
            
            # Test 2: Create second device (should succeed)
            try:
                device2, config2 = WireGuardManager.create_device_config(test_user, "Test Device 2")
                print(f"  ✓ Created device 2: {device2.device_name} ({device2.wg_ip_address})")
            except Exception as e:
                print(f"  ❌ Failed to create device 2: {e}")
                return False
            
            # Test 3: Try to create third device (should FAIL - limit reached)
            try:
                device3, config3 = WireGuardManager.create_device_config(test_user, "Test Device 3")
                print(f"  ❌ PROBLEM: Created device 3 but should have been blocked!")
                return False
            except Exception as e:
                if "maximum device limit" in str(e).lower():
                    print(f"  ✓ Correctly blocked device 3 (limit enforced!)")
                else:
                    print(f"  ⚠️  Device 3 blocked but unexpected error: {e}")
            
            # Test 4: Verify each device has unique keys and IPs
            if device1.wg_public_key == device2.wg_public_key:
                print(f"  ❌ PROBLEM: Devices have same public key!")
                return False
            if device1.wg_ip_address == device2.wg_ip_address:
                print(f"  ❌ PROBLEM: Devices have same IP address!")
                return False
            print(f"  ✓ Devices have unique keys and IPs")
            
            # Clean up
            Device.query.filter_by(user_id=test_user.id).delete()
            db.session.delete(test_user)
            db.session.commit()
            print(f"  ✓ Cleaned up test data")
            
            print("✅ Device creation and limits working correctly!\n")
            return True
            
        except Exception as e:
            print(f"❌ Device creation error: {e}\n")
            return False

def test_connection_monitoring():
    """Test connection monitoring functions"""
    print("Testing connection monitoring...")
    
    with app.app_context():
        try:
            # Test that the function exists and runs
            WireGuardManager.update_device_connection_status()
            print("  ✓ Connection status update function works")
            
            # Test peer statistics
            peers = WireGuardManager.get_peer_statistics()
            print(f"  ✓ Peer statistics function works ({len(peers)} peers found)")
            
            print("✅ Connection monitoring functions working!\n")
            return True
            
        except Exception as e:
            print(f"❌ Monitoring error: {e}\n")
            return False

def test_device_config_generation():
    """Test generating device configs"""
    print("Testing device config generation...")
    
    with app.app_context():
        try:
            # Check WireGuard server config exists
            wg_config = WireGuardConfig.query.first()
            if not wg_config:
                print("  ⚠️  No WireGuard server config found (run init_db.py first)")
                return True  # Not a failure, just not initialized
            
            print(f"  ✓ WireGuard server config exists")
            
            # Test generating server config with devices
            config = WireGuardManager.update_server_config_with_devices()
            assert '[Interface]' in config
            assert '[Peer]' in config or len(Device.query.all()) == 0
            print(f"  ✓ Server config generation works")
            
            print("✅ Config generation working!\n")
            return True
            
        except Exception as e:
            print(f"❌ Config generation error: {e}\n")
            return False

def main():
    print("="*60)
    print("WIREGUARD DEVICE MANAGEMENT SYSTEM TEST")
    print("="*60)
    print()
    
    tests = [
        test_database_schema,
        test_device_creation,
        test_connection_monitoring,
        test_device_config_generation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test crashed: {e}\n")
            results.append(False)
    
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All tests passed ({passed}/{total})")
        print("\nYour system is ready to use!")
        print("Run: sudo ./setup_device_management.sh")
    else:
        print(f"⚠️  {passed}/{total} tests passed")
        print("\nSome issues were found. Please review the errors above.")
    
    return passed == total

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
