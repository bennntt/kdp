#!/usr/bin/env python3
"""
Setup External MySQL Database (db4free.net)
"""

import pymysql
from datetime import datetime
from werkzeug.security import generate_password_hash

def setup_external_database():
    """Setup external MySQL database"""
    try:
        print("🚀 Setting up External MySQL Database...")
        print("=" * 50)
        
        # Database connection details
        db_config = {
            'host': 'db4free.net',
            'user': 'userkdpdbs',
            'password': '97dccde968',
            'database': 'kdpdbs',
            'port': 3306,
            'charset': 'utf8mb4'
        }
        
        print("🔌 Connecting to external MySQL server...")
        print(f"   Host: {db_config['host']}")
        print(f"   Database: {db_config['database']}")
        print(f"   User: {db_config['user']}")
        
        # Test connection
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        connection.close()
        print("✅ Connection successful!")
        
        # Now use Flask app to create tables
        print("🏗️  Creating tables using Flask...")
        from app import create_app, db
        from models import User, ToolConfiguration
        
        app = create_app()
        
        with app.app_context():
            # Create all tables
            print("📋 Creating database tables...")
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
            
            # Create premium test user
            premium_exists = User.query.filter_by(email='premium@kdptools.com').first()
            if not premium_exists:
                print("💎 Creating premium test user...")
                premium_user = User(
                    email='premium@kdptools.com',
                    username='premiumuser',
                    password_hash=generate_password_hash('premium123'),
                    first_name='Premium',
                    last_name='User',
                    is_admin=False,
                    subscription_type='monthly',
                    email_verified=True,
                    created_at=datetime.utcnow()
                )
                db.session.add(premium_user)
                db.session.commit()
                print("✅ Premium user created!")
            else:
                print("ℹ️  Premium user already exists")
            
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
            free_tools = ToolConfiguration.query.filter_by(requires_paid_plan=False).count()
            paid_tools = ToolConfiguration.query.filter_by(requires_paid_plan=True).count()
            
            print("\n" + "=" * 50)
            print("🎉 External Database Setup Complete!")
            print("=" * 50)
            
            print(f"\n📊 Database Summary:")
            print(f"   🌐 Host: db4free.net")
            print(f"   🗄️  Database: kdpdbs")
            print(f"   👥 Total Users: {user_count}")
            print(f"   👑 Admin Users: {admin_count}")
            print(f"   🛠️  Total Tools: {tool_count}")
            print(f"   🆓 Free Tools: {free_tools}")
            print(f"   👑 Premium Tools: {paid_tools}")
            
            print(f"\n🔑 Login Credentials:")
            print(f"   👑 Admin: admin@kdptools.com / admin123")
            print(f"   👤 Free User: test@kdptools.com / test123")
            print(f"   💎 Premium User: premium@kdptools.com / premium123")
            
            print(f"\n🌐 Ready to start:")
            print(f"   Command: python app.py")
            print(f"   URL: http://localhost:5000")
            
            print(f"\n📝 Database URL:")
            print(f"   DATABASE_URL=mysql+pymysql://userkdpdbs:97dccde968@db4free.net:3306/kdpdbs")
            
            return True
            
    except pymysql.Error as e:
        print(f"❌ MySQL Error: {e}")
        print("\n🔧 Possible issues:")
        print("   - Check internet connection")
        print("   - Verify database credentials")
        print("   - db4free.net might be temporarily unavailable")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_external_connection():
    """Test connection to external database"""
    try:
        print("🔍 Testing connection to external database...")
        
        connection = pymysql.connect(
            host='db4free.net',
            user='userkdpdbs',
            password='97dccde968',
            database='kdpdbs',
            port=3306,
            charset='utf8mb4',
            connect_timeout=10
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        cursor.close()
        connection.close()
        
        print(f"✅ Connection successful!")
        print(f"   MySQL Version: {version[0]}")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing external database connection...")
    if test_external_connection():
        success = setup_external_database()
        if not success:
            print("\n❌ Database setup failed!")
        else:
            print("\n🎊 Setup completed successfully!")
    else:
        print("\n❌ Cannot connect to external database!")