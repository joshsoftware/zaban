#!/usr/bin/env python3
"""
Script to create a dummy user in the database for testing.
"""

import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.db.database import Base
import os

# Load environment variables
load_dotenv()

def create_dummy_user(email: str, first_name: str = "Test", last_name: str = "User"):
    """Create a dummy user in the database."""
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[ERROR] DATABASE_URL not found in environment variables")
        sys.exit(1)
    
    # Create engine and session
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"[WARNING] User with email '{email}' already exists!")
            print(f"   ID: {existing_user.id}")
            print(f"   Name: {existing_user.first_name} {existing_user.last_name}")
            print(f"   Active: {existing_user.is_active}")
            return existing_user
        
        # Create new user
        new_user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            is_verified=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print("[SUCCESS] Dummy user created successfully!")
        print(f"   ID: {new_user.id}")
        print(f"   Email: {new_user.email}")
        print(f"   Name: {new_user.first_name} {new_user.last_name}")
        print(f"   Active: {new_user.is_active}")
        print(f"   Verified: {new_user.is_verified}")
        print(f"   Created: {new_user.created_at}")
        
        return new_user
        
    except Exception as e:
        print(f"[ERROR] Error creating user: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


def list_users():
    """List all users in the database."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[ERROR] DATABASE_URL not found in environment variables")
        sys.exit(1)
    
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        users = db.query(User).all()
        if not users:
            print("[INFO] No users found in database")
            return
        
        print(f"\n[INFO] Found {len(users)} user(s) in database:\n")
        for user in users:
            print(f"   * {user.email}")
            print(f"     ID: {user.id}")
            print(f"     Name: {user.first_name} {user.last_name}")
            print(f"     Active: {user.is_active}, Verified: {user.is_verified}")
            print()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Zaban Dummy User Creator")
    print("=" * 50 + "\n")
    
    # Default test user
    default_email = "test@joshsoftware.com"
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_users()
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("Usage:")
            print("  python create_dummy_user.py                    # Create default test user")
            print("  python create_dummy_user.py <email>           # Create user with custom email")
            print("  python create_dummy_user.py <email> <first> <last>  # Create user with full details")
            print("  python create_dummy_user.py list              # List all users")
            print("\nExample:")
            print("  python create_dummy_user.py test@example.com John Doe")
        else:
            email = sys.argv[1]
            first_name = sys.argv[2] if len(sys.argv) > 2 else "Test"
            last_name = sys.argv[3] if len(sys.argv) > 3 else "User"
            create_dummy_user(email, first_name, last_name)
    else:
        create_dummy_user(default_email, "Test", "User")
    
    print("\n[TIP] You can now use this email to generate JWT tokens for testing!")

