#!/usr/bin/env python3
"""
Initialize VM Resource Intelligence System with historical data
"""
import psycopg2
from datetime import datetime, timedelta
import sys

DB_HOST = "10.251.150.222"
DB_PORT = "5210"
DB_NAME = "sangfor_scp"
DB_USER = "apirak"
DB_PASS = "Kanokwan@1987#neostar"

def main():
    print("=" * 60)
    print("VM Resource Intelligence - Data Initialization")
    print("=" * 60)
    
    # Connect to database
    print(f"\n[1/3] Connecting to database...")
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
    
    # Generate daily statistics for last 30 days
    print(f"\n[2/3] Generating daily statistics for last 30 days...")
    try:
        today = datetime.now().date()
        days_generated = 0
        
        for i in range(30, -1, -1):
            target_date = today - timedelta(days=i)
            cursor.execute(
                "SELECT vmreport.aggregate_daily_stats(%s)",
                (target_date,)
            )
            result = cursor.fetchone()
            if result:
                vms_processed, records_created = result[0].strip('()').split(',')
                print(f"  ✓ {target_date}: {records_created} records created for {vms_processed} VMs")
                days_generated += 1
        
        conn.commit()
        print(f"\n✓ Generated statistics for {days_generated} days")
    except Exception as e:
        conn.rollback()
        print(f"✗ Failed to generate daily statistics: {e}")
        cursor.close()
        conn.close()
        return False
    
    # Calculate health scores for all VMs
    print(f"\n[3/3] Calculating health scores for all VMs...")
    try:
        # Get count of VMs
        cursor.execute("""
            SELECT COUNT(*) 
            FROM sangfor.vm_master 
            WHERE is_deleted = FALSE
        """)
        vm_count = cursor.fetchone()[0]
        print(f"  Found {vm_count} active VMs")
        
        # Calculate health scores
        cursor.execute("""
            INSERT INTO vmreport.vm_health_score (
                vm_uuid, health_score, risk_level, cpu_score, memory_score,
                disk_score, network_score, issues, recommendations,
                is_over_provisioned, is_idle, has_spike
            )
            SELECT 
                vm.vm_uuid,
                (vmreport.calculate_vm_health_score(vm.vm_uuid)).*
            FROM sangfor.vm_master vm
            WHERE vm.is_deleted = FALSE
        """)
        
        rows_affected = cursor.rowcount
        conn.commit()
        print(f"✓ Calculated health scores for {rows_affected} VMs")
    except Exception as e:
        conn.rollback()
        print(f"✗ Failed to calculate health scores: {e}")
        print(f"Error details: {str(e)}")
        cursor.close()
        conn.close()
        return False
    
    # Refresh materialized view
    print(f"\n[4/4] Refreshing executive summary view...")
    try:
        cursor.execute("REFRESH MATERIALIZED VIEW vmreport.mv_vm_executive_summary")
        conn.commit()
        print(f"✓ Materialized view refreshed")
    except Exception as e:
        conn.rollback()
        print(f"✗ Failed to refresh view: {e}")
        cursor.close()
        conn.close()
        return False
    
    # Summary
    print("\n" + "=" * 60)
    print("Data initialization completed successfully!")
    print("=" * 60)
    
    # Show some statistics
    print(f"\nCurrent statistics:")
    cursor.execute("""
        SELECT 
            COUNT(*) as total_records,
            MIN(date) as earliest_date,
            MAX(date) as latest_date
        FROM vmreport.vm_resource_daily
    """)
    stats = cursor.fetchone()
    if stats:
        print(f"  - Daily records: {stats[0]}")
        print(f"  - Date range: {stats[1]} to {stats[2]}")
    
    cursor.execute("""
        SELECT COUNT(*) 
        FROM vmreport.vm_health_score
    """)
    health_count = cursor.fetchone()[0]
    print(f"  - Health scores: {health_count}")
    
    cursor.execute("""
        SELECT COUNT(*) 
        FROM vmreport.mv_vm_executive_summary
    """)
    summary_count = cursor.fetchone()[0]
    print(f"  - Executive summary VMs: {summary_count}")
    
    cursor.close()
    conn.close()
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
