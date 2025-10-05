"""
Script to create an admin user for the AuraFlix admin panel.
Run this script to create your first admin user.

Usage:
    python create_admin.py
"""

from app.database import SessionLocal
from app.models import User
from app.utils.password import hash_password


def create_admin_user(
    email: str, password: str, first_name: str = None, last_name: str = None
):
    """Create an admin user in the database."""
    db = SessionLocal()
    try:
        # Check if user already exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"❌ User with email {email} already exists!")
            if existing.is_admin:
                print("✓ User is already an admin.")
            else:
                # Promote to admin
                existing.is_admin = True
                existing.is_verified = True
                db.commit()
                print("✓ User promoted to admin!")
            return existing

        # Create new admin user
        hashed_password = hash_password(password)
        admin_user = User(
            email=email,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            is_admin=True,
            is_verified=True,  # Auto-verify admin users
            is_active=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print("✅ Admin user created successfully!")
        print(f"   Email: {email}")
        print(f"   Name: {first_name} {last_name}")
        print(f"   Admin: {admin_user.is_admin}")
        return admin_user
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("AuraFlix - Create Admin User")
    print("=" * 50)

    email = input("Enter admin email: ").strip()
    password = input("Enter admin password: ").strip()
    first_name = input("Enter first name (optional): ").strip() or None
    last_name = input("Enter last name (optional): ").strip() or None

    if not email or not password:
        print("❌ Email and password are required!")
        exit(1)

    create_admin_user(email, password, first_name, last_name)

    print("\n" + "=" * 50)
    print("Admin Panel Access:")
    print("URL: http://localhost:8000/admin")
    print(f"Username: {email}")
    print("Password: [the password you just entered]")
    print("=" * 50)
