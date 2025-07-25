#!/usr/bin/env python3
"""
Simple Database Creation Script
"""

from datetime import datetime
from werkzeug.security import generate_password_hash

def create_database():
    """Create database with basic setup"""
    try:
        print("🚀 Creating KDP Tools Hub Database...")
        
        from app import create_app, db
        from models import User
        
        app = create_app()
        
        with app.app_context():
            # Create all tables
            print("📋 Creating tables...")
            db.create_all()
            print("✅ Tables created!")
            
            # Create admin user
            admin_exists = User.query.filter_by(email='admin@kdptools.com').first()
            if not admin_exists:
                print("👑 Creating admin user...")
                admin = User(
                    email='admin@kdptools.com',
                    username='admin',
                    password_hash=generate_password_hash('admin123'),
                    first_name='Admin',
                    last_name='User',
                    is_admin=True,
                    subscription_type='yearly',
                    email_verified=True,
                    created_at=datetime.utcnow()
                )
                db.session.add(admin)
                db.session.commit()
                print("✅ Admin user created!")
            else:
                print("ℹ️  Admin user already exists")
            
            # Create test user
            test_exists = User.query.filter_by(email='test@kdptools.com').first()
            if not test_exists:
                print("👤 Creating test user...")
                test_user = User(
                    email='test@kdptools.com',
                    username='testuser',
                    password_hash=generate_password_hash('test123'),
                    first_name='Test',
                    last_name='User',
                    is_admin=False,
                    subscription_type='free',
                    email_verified=True,
                    created_at=datetime.utcnow()
                )
                db.session.add(test_user)
                db.session.commit()
                print("✅ Test user created!")
            else:
                print("ℹ️  Test user already exists")
            
            # Show database summary
            user_count = User.query.count()
            admin_count = User.query.filter_by(is_admin=True).count()
            print(f"\n📊 Database Summary:")
            print(f"   👥 Total Users: {user_count}")
            print(f"   👑 Admin Users: {admin_count}")
            
            print("\n🎉 Database created successfully!")
            print("\n🔑 Login Credentials:")
            print("   👑 Admin: admin@kdptools.com / admin123")
            print("   👤 Test: test@kdptools.com / test123")
            print("\n🌐 Start app: python app.py")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_database()