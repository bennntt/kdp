#!/usr/bin/env python3
"""
Database Initialization Script
Creates all tables and adds default data
"""

import os
import sys
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def init_database():
    """Initialize database with tables and default data"""
    try:
        from app import create_app
        from models import db, User, ToolConfiguration
        
        print("🚀 KDP Tools Hub - Database Initialization")
        print("=" * 60)
        
        # Create Flask app
        app = create_app()
        
        with app.app_context():
            print("📋 Creating database tables...")
            
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Create default admin user
            admin_user = User.query.filter_by(email='admin@kdptools.com').first()
            
            if not admin_user:
                print("👑 Creating default admin user...")
                
                admin_user = User(
                    email='admin@kdptools.com',
                    username='admin',
                    password_hash=generate_password_hash('admin123'),
                    first_name='Admin',
                    last_name='User',
                    is_admin=True,
                    is_active=True,
                    subscription_type='yearly',
                    subscription_start=datetime.utcnow(),
                    subscription_end=datetime.utcnow() + timedelta(days=365),
                    email_verified=True,
                    theme_preference='dark',
                    language_preference='en',
                    timezone_preference='UTC',
                    created_at=datetime.utcnow()
                )
                
                db.session.add(admin_user)
                db.session.commit()
                
                print("✅ Admin user created successfully!")
                print("   📧 Email: admin@kdptools.com")
                print("   🔑 Password: admin123")
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
                
                print("✅ Test user created successfully!")
                print("   📧 Email: test@kdptools.com")
                print("   🔑 Password: test123")
            else:
                print("ℹ️  Test user already exists")
            
            # Create premium test user
            premium_user = User.query.filter_by(email='premium@kdptools.com').first()
            
            if not premium_user:
                print("💎 Creating premium test user...")
                
                premium_user = User(
                    email='premium@kdptools.com',
                    username='premiumuser',
                    password_hash=generate_password_hash('premium123'),
                    first_name='Premium',
                    last_name='User',
                    is_admin=False,
                    subscription_type='monthly',
                    subscription_start=datetime.utcnow(),
                    subscription_end=datetime.utcnow() + timedelta(days=30),
                    email_verified=True,
                    created_at=datetime.utcnow()
                )
                
                db.session.add(premium_user)
                db.session.commit()
                
                print("✅ Premium user created successfully!")
                print("   📧 Email: premium@kdptools.com")
                print("   🔑 Password: premium123")
            else:
                print("ℹ️  Premium user already exists")
            
            # Create default tools
            if ToolConfiguration.query.count() == 0:
                print("🛠️  Creating default tools...")
                ToolConfiguration.create_default_tools()
                print("✅ Default tools created successfully!")
            else:
                print("ℹ️  Tools already exist")
            
            print("\n" + "=" * 60)
            print("🎉 Database initialization completed successfully!")
            print("=" * 60)
            
            print("\n📊 Database Summary:")
            print(f"   👥 Total Users: {User.query.count()}")
            print(f"   👑 Admin Users: {User.query.filter_by(is_admin=True).count()}")
            print(f"   🛠️  Total Tools: {ToolConfiguration.query.count()}")
            print(f"   🆓 Free Tools: {ToolConfiguration.query.filter_by(requires_paid_plan=False).count()}")
            print(f"   👑 Premium Tools: {ToolConfiguration.query.filter_by(requires_paid_plan=True).count()}")
            
            print("\n🔑 Login Credentials:")
            print("   👑 Admin: admin@kdptools.com / admin123")
            print("   👤 Free User: test@kdptools.com / test123")
            print("   💎 Premium User: premium@kdptools.com / premium123")
            
            print("\n🛠️  Available Tools:")
            tools = ToolConfiguration.query.order_by(ToolConfiguration.sort_order).all()
            for tool in tools:
                status = "👑 Premium" if tool.requires_paid_plan else "🆓 Free"
                print(f"   {tool.sort_order}. {tool.display_name} - {status}")
            
            print("\n🌐 Ready to start the application!")
            print("   Command: python app.py")
            print("   URL: http://localhost:5000")
            
            return True
            
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_database():
    """Check if database is working"""
    try:
        from app import create_app
        from models import db, User, ToolConfiguration
        
        app = create_app()
        
        with app.app_context():
            user_count = User.query.count()
            admin_exists = User.query.filter_by(is_admin=True).first() is not None
            tools_count = ToolConfiguration.query.count()
            
            print("✅ Database is working!")
            print(f"   👥 Users: {user_count}")
            print(f"   👑 Admin exists: {'Yes' if admin_exists else 'No'}")
            print(f"   🛠️  Tools: {tools_count}")
            
            return user_count > 0 and admin_exists and tools_count > 0
            
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Checking database status...")
    
    if check_database():
        print("\n✅ Database is already initialized!")
        print("🌐 You can start the application: python app.py")
    else:
        print("\n🔧 Database needs initialization...")
        success = init_database()
        
        if success:
            print("\n🎊 Initialization completed successfully!")
        else:
            print("\n❌ Initialization failed!")
            sys.exit(1)