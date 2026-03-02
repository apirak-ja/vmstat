#!/usr/bin/env python3
"""
Install VM Resource Intelligence Schema
"""
import psycopg2
import os
import sys

# Database connection parameters from .env
DB_HOST = "10.251.150.222"
DB_PORT = "5210"
DB_NAME = "sangfor_scp"
DB_USER = "apirak"
DB_PASS = "Kanokwan@1987#neostar"

def main():
    print("=" * 60)
    print("VM Resource Intelligence System - Database Installation")
    print("=" * 60)
    
    # Read SQL file
    sql_file = "database/schema/20_vm_resource_intelligence.sql"
    print(f"\n[1/3] Reading SQL file: {sql_file}")
    
    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        print(f"✓ SQL file loaded ({len(sql)} characters)")
    except Exception as e:
        print(f"✗ Failed to read SQL file: {e}")
        return False
    
    # Connect to database
    print(f"\n[2/3] Connecting to database: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    
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
        print(f"✓ Connected successfully")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False
    
    # Execute SQL
    print(f"\n[3/3] Executing SQL statements...")
    
    try:
        cursor.execute(sql)
        conn.commit()
        print(f"✓ Schema installed successfully")
        
        # Verify installation
        cursor.execute("""
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE schemaname = 'vmreport'
            ORDER BY tablename
        """)
        tables = cursor.fetchall()
        
        print(f"\n✓ Created {len(tables)} tables:")
        for schema, table in tables:
            print(f"  - {schema}.{table}")
        
        # Check materialized views
        cursor.execute("""
            SELECT schemaname, matviewname 
            FROM pg_matviews 
            WHERE schemaname = 'vmreport'
        """)
        views = cursor.fetchall()
        
        if views:
            print(f"\n✓ Created {len(views)} materialized views:")
            for schema, view in views:
                print(f"  - {schema}.{view}")
        
        # Check functions
        cursor.execute("""
            SELECT routine_schema, routine_name 
            FROM information_schema.routines 
            WHERE routine_schema = 'vmreport'
            AND routine_type = 'FUNCTION'
        """)
        functions = cursor.fetchall()
        
        if functions:
            print(f"\n✓ Created {len(functions)} functions:")
            for schema, func in functions:
                print(f"  - {schema}.{func}()")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("Installation completed successfully!")
        print("=" * 60)
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Execution failed: {e}")
        print(f"\nError details:")
        print(str(e))
        cursor.close()
        conn.close()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
