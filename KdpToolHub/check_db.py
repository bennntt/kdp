#!/usr/bin/env python3
"""
Check Database Script
"""

import os
import sqlite3

def check_database():
    """Check database status"""
    db_path = 'kdp_tools.db'
    
    if not os.path.exists(db_path):
        print("❌ Database file does not exist!")
        return False
    
    print(f"✅ Database file exists: {os.path.getsize(db_path)} bytes")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n📊 Database Tables ({len(tables)} total):")
        print("=" * 50)
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"🗂️  {table_name}: {count} records")
            
            # Show sample data for user table
            if table_name == 'user' and count > 0:
                cursor.execute("SELECT email, username, is_admin FROM user")
                users = cursor.fetchall()
                print("   👥 Users:")
                for user in users:
                    role = "👑 Admin" if user[2] else "👤 User"
                    print(f"      {role}: {user[0]} ({user[1]})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    check_database()