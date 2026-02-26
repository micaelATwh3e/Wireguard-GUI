#!/usr/bin/env python3
"""
Migration script to add max_connections field to existing User table
Run this once to update existing database
"""

from app import app, db
from models import User
from sqlalchemy import text

def migrate():
    with app.app_context():
        try:
            # Check if column already exists
            result = db.session.execute(text(
                "SELECT COUNT(*) FROM pragma_table_info('users') WHERE name='max_connections'"
            ))
            exists = result.scalar() > 0
            
            if exists:
                print("✓ Column 'max_connections' already exists")
                return
            
            # Add the column
            print("Adding 'max_connections' column to users table...")
            db.session.execute(text(
                "ALTER TABLE users ADD COLUMN max_connections INTEGER DEFAULT 1"
            ))
            db.session.commit()
            
            # Update existing users to have default value
            print("Setting default max_connections for existing users...")
            db.session.execute(text(
                "UPDATE users SET max_connections = 1 WHERE max_connections IS NULL"
            ))
            db.session.commit()
            
            print("✓ Migration completed successfully!")
            print(f"  - All users now have max_connections set to 1")
            
        except Exception as e:
            print(f"✗ Migration failed: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate()
