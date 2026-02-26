#!/usr/bin/env python3
"""
Migration script to add allowed_source_ips column to users table
"""

from app import app
from models import db, User
from sqlalchemy import text

def migrate():
    with app.app_context():
        try:
            # Check if column already exists
            result = db.session.execute(text(
                "SELECT COUNT(*) FROM pragma_table_info('users') WHERE name='allowed_source_ips'"
            ))
            count = result.scalar()
            
            if count > 0:
                print("✓ Column 'allowed_source_ips' already exists in users table")
                return True
            
            # Add the column
            print("Adding 'allowed_source_ips' column to users table...")
            db.session.execute(text(
                "ALTER TABLE users ADD COLUMN allowed_source_ips TEXT"
            ))
            db.session.commit()
            
            print("✓ Successfully added 'allowed_source_ips' column")
            print("✓ Migration completed successfully")
            return True
            
        except Exception as e:
            print(f"✗ Migration failed: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("=" * 60)
    print("Database Migration: Add allowed_source_ips to users")
    print("=" * 60)
    
    if migrate():
        print("\n✓ All migrations completed successfully!")
    else:
        print("\n✗ Migration failed. Please check the error message above.")
        exit(1)
