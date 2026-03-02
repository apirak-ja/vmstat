#!/usr/bin/env python3
"""
Add Reports menu to the system
"""
import psycopg2
import sys

DB_HOST = "10.251.150.222"
DB_PORT = "5210"
DB_NAME = "sangfor_scp"
DB_USER = "apirak"
DB_PASS = "Kanokwan@1987#neostar"

def main():
    print("=" * 60)
    print("Adding 'Reports' menu to VM Resource Intelligence System")
    print("=" * 60)
    
    # Read SQL file
    sql_file = "database/add_reports_menu.sql"
    print(f"\n[1/2] Reading SQL file: {sql_file}")
    
    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        print(f"✓ SQL file loaded")
    except Exception as e:
        print(f"✗ Failed to read SQL file: {e}")
        return False
    
    # Connect and execute
    print(f"\n[2/2] Executing SQL...")
    
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        conn.autocommit = False
        cursor = conn.cursor()
        
        cursor.execute(sql)
        
        # Get verification result
        result = cursor.fetchone()
        if result:
            print(f"\n✓ {result[0]}")
            print(f"✓ {result[1]}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("'Reports' menu added successfully!")
        print("=" * 60)
        print("\nMenu details:")
        print("  - Name: Reports")
        print("  - Path: /vmreport")
        print("  - Icon: Assessment")
        print("  - Order: 7")
        print("\nPermissions:")
        print("  - Admin: View, Edit, Delete")
        print("  - Manager: View, Edit")
        print("  - Viewer: View only")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"✗ Execution failed: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
