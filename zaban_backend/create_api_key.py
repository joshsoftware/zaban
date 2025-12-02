#!/usr/bin/env python3
"""
Script to create an API key for a user directly in the database.
"""

import sys
import secrets
import hashlib
import hmac
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.models.api_key import ApiKey
import os

# Load environment variables
load_dotenv()


def hash_key(secret_key: str) -> str:
    """Hash the API key for storage using HMAC (same as backend)."""
    # Use the same pepper as the backend
    pepper = os.getenv("API_KEY_PEPPER", "")
    return hmac.new(pepper.encode("utf-8"), secret_key.encode("utf-8"), hashlib.sha256).hexdigest()


def generate_api_key() -> str:
    """Generate a new API key with sk- prefix."""
    return f"sk-{secrets.token_urlsafe(32)}"


def create_api_key_for_user(email: str, key_name: str = "Test API Key"):
    """Create an API key for a user."""
    
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
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"[ERROR] User with email '{email}' not found!")
            print("\nTip: Run 'python create_dummy_user.py list' to see available users")
            sys.exit(1)
        
        # Generate new API key
        secret_key = generate_api_key()
        key_hash = hash_key(secret_key)
        
        # Create API key record
        api_key = ApiKey(
            user_id=user.id,
            name=key_name,
            key_hash=key_hash,
            is_active=True
        )
        
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        
        print("[SUCCESS] API Key created successfully!")
        print(f"\n   User: {user.email}")
        print(f"   Key Name: {api_key.name}")
        print(f"   Key ID: {api_key.id}")
        print(f"   Active: {api_key.is_active}")
        print(f"   Created: {api_key.created_at}")
        print(f"\n   SECRET KEY (save this, it won't be shown again):")
        print(f"   {secret_key}")
        print("\n" + "=" * 70)
        print("IMPORTANT: Copy the secret key above now!")
        print("This is the only time it will be displayed.")
        print("=" * 70)
        
        return api_key, secret_key
        
    except Exception as e:
        print(f"[ERROR] Error creating API key: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


def list_api_keys(email: str = None):
    """List API keys, optionally filtered by user email."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[ERROR] DATABASE_URL not found in environment variables")
        sys.exit(1)
    
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        if email:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                print(f"[ERROR] User with email '{email}' not found!")
                return
            keys = db.query(ApiKey).filter(ApiKey.user_id == user.id).all()
            print(f"\n[INFO] API Keys for user: {email}\n")
        else:
            keys = db.query(ApiKey).all()
            print(f"\n[INFO] All API Keys in database:\n")
        
        if not keys:
            print("[INFO] No API keys found")
            return
        
        for key in keys:
            key_user = db.query(User).filter(User.id == key.user_id).first()
            print(f"   * {key.name}")
            print(f"     ID: {key.id}")
            print(f"     User: {key_user.email if key_user else 'Unknown'}")
            print(f"     Active: {key.is_active}")
            print(f"     Created: {key.created_at}")
            if key.revoked_at:
                print(f"     Revoked: {key.revoked_at}")
            print()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 70)
    print("Zaban API Key Creator")
    print("=" * 70 + "\n")
    
    default_email = "test@joshsoftware.com"
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            email = sys.argv[2] if len(sys.argv) > 2 else None
            list_api_keys(email)
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("Usage:")
            print("  python create_api_key.py                        # Create key for default user")
            print("  python create_api_key.py <email>               # Create key for specific user")
            print("  python create_api_key.py <email> <name>        # Create key with custom name")
            print("  python create_api_key.py list                  # List all API keys")
            print("  python create_api_key.py list <email>          # List keys for specific user")
            print("\nExample:")
            print("  python create_api_key.py test@joshsoftware.com 'Production Key'")
        else:
            email = sys.argv[1]
            key_name = sys.argv[2] if len(sys.argv) > 2 else "Test API Key"
            create_api_key_for_user(email, key_name)
    else:
        create_api_key_for_user(default_email)
    
    print("\n[TIP] Use this API key in the X-API-Key header for API requests!")

