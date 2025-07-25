#!/usr/bin/env python3
"""
Check database_kdp Status
"""

import pymysql

def check_database_kdp():
    """Check database_kdp status"""
    try:
        print("🔍 Checking database_kdp Status...")
        print("=" * 50)
        
        # Connect to database
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='database_kdp',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print(f"📊 Database: database_kdp")
        print(f"🗂️  Tables: {len(tables)} total")
        print("-" * 30)
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"📋 {table_name}: {count} records")
            
            # Show sample data for important tables
            if table_name == 'user' and count > 0:
                cursor.execute("SELECT email, username, is_admin FROM user")
                users = cursor.fetchall()
                print("   👥 Users:")
                for user in users:
                    role = "👑 Admin" if user[2] else "👤 User"
                    print(f"      {role}: {user[0]} ({user[1]})")
            
            elif table_name == 'tool_configuration' and count > 0:
                cursor.execute("SELECT tool_name, display_name, requires_paid_plan FROM tool_configuration ORDER BY sort_order")
                tools = cursor.fetchall()
                print("   🛠️  Tools:")
                for tool in tools:
                    status = "👑 Premium" if tool[2] else "🆓 Free"
                    print(f"      {status}: {tool[1]} ({tool[0]})")
        
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 50)
        print("✅ Database is working perfectly!")
        print("📝 Database URL: mysql+pymysql://root:@localhost/database_kdp")
        print("🌐 Ready to start: python app.py")
        
        return True
        
    except pymysql.Error as e:
        print(f"❌ MySQL Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_database_kdp()