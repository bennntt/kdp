#!/usr/bin/env python3
"""
Setup database_kdp for XAMPP
"""

import pymysql
from datetime import datetime
from werkzeug.security import generate_password_hash

def setup_database_kdp():
    """Setup database_kdp in MySQL"""
    try:
        print("🚀 Setting up database_kdp for XAMPP...")
        print("=" * 50)
        
        # Connect to MySQL server (without database)
        print("🔌 Connecting to MySQL server...")
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',  # Default XAMPP MySQL password is empty
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Create database if not exists
        print("📋 Creating database 'database_kdp'...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS database_kdp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute("USE database_kdp")
        print("✅ Database 'database_kdp' created/selected!")
        
        # Close initial connection
        cursor.close()
        connection.close()
        
        # Now use Flask app to create tables
        print("🏗️  Creating tables using Flask...")
        from app import create_app, db
        from models import User, ToolConfiguration
        
        app = create_app()
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ All tables created!")
            
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
            
            # Create default tools
            print("🛠️  Creating default tools...")
            try:
                if ToolConfiguration.query.count() == 0:
                    ToolConfiguration.create_default_tools()
                    print("✅ Default tools created!")
                else:
                    print("ℹ️  Tools already exist")
            except Exception as e:
                print(f"⚠️  Tools creation: {e}")
            
            # Show summary
            user_count = User.query.count()
            admin_count = User.query.filter_by(is_admin=True).count()
            tool_count = ToolConfiguration.query.count()
            
            print("\n" + "=" * 50)
            print("🎉 Database Setup Complete!")
            print("=" * 50)
            
            print(f"\n📊 Database Summary:")
            print(f"   🗄️  Database: database_kdp")
            print(f"   👥 Total Users: {user_count}")
            print(f"   👑 Admin Users: {admin_count}")
            print(f"   🛠️  Total Tools: {tool_count}")
            
            print(f"\n🔑 Login Credentials:")
            print(f"   👑 Admin: admin@kdptools.com / admin123")
            print(f"   👤 Test: test@kdptools.com / test123")
            
            print(f"\n🌐 Ready to start:")
            print(f"   Command: python app.py")
            print(f"   URL: http://localhost:5000")
            
            print(f"\n📝 Database URL:")
            print(f"   DATABASE_URL=mysql+pymysql://root:@localhost/database_kdp")
            
            return True
            
    except pymysql.Error as e:
        print(f"❌ MySQL Error: {e}")
        print("\n🔧 Make sure XAMPP is running and MySQL service is started!")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_xampp_status():
    """Check if XAMPP MySQL is running"""
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            connect_timeout=5
        )
        connection.close()
        print("✅ XAMPP MySQL is running!")
        return True
    except:
        print("❌ XAMPP MySQL is not running!")
        print("🔧 Please start XAMPP and make sure MySQL service is running.")
        return False

if __name__ == "__main__":
    print("🔍 Checking XAMPP status...")
    if check_xampp_status():
        success = setup_database_kdp()
        if not success:
            print("\n❌ Database setup failed!")
        else:
            print("\n🎊 Setup completed successfully!")
    else:
        print("\n❌ Please start XAMPP first!")