#!/usr/bin/env python3
"""
Simple Database Setup Script
Creates tables and default data
"""

import os
import sys
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

def setup_tables_and_admin():
    """Setup database tables and create admin user"""
    try:
        print("🚀 Setting up KDP Tools Hub Database...")
        print("=" * 50)
        
        # Import after ensuring path
        from app import create_app, db
        from models import User, ToolConfiguration
        
        app = create_app()
        
        with app.app_context():
            print("📋 Creating database tables...")
            db.create_all()
            print("✅ Database tables created!")
            
            # Create admin user
            admin_user = User.query.filter_by(email='admin@kdptools.com').first()
            if not admin_user:
                print("👑 Creating admin user...")
                admin_user = User(
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
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Admin user created!")
            else:
                print("ℹ️  Admin user already exists")
            
            # Create test user
            test_user = User.query.filter_by(email='test@kdptools.com').first()
            if not test_user:
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
            
            # Create default tools
            print("🛠️  Creating default tools...")
            try:
                ToolConfiguration.create_default_tools()
                print("✅ Default tools created!")
            except Exception as e:
                print(f"⚠️  Tools creation: {e}")
            
            print("\n" + "=" * 50)
            print("🎉 Database setup completed!")
            print("=" * 50)
            
            print("\n🔑 Login Credentials:")
            print("   👑 Admin: admin@kdptools.com / admin123")
            print("   👤 Test: test@kdptools.com / test123")
            
            print("\n🌐 Start the application:")
            print("   python app.py")
            print("   http://localhost:5000")
            
            return True
            
    except Exception as e:
        print(f"❌ Error setting up tables and admin: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = setup_tables_and_admin()
    if not success:
        print("❌ Failed to setup tables and admin user.")
        sys.exit(1)
    else:
        print("✅ Setup completed successfully!")