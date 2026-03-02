#!/usr/bin/env python3
"""
VM Resource Intelligence System - Background Job Scheduler
รันตัวนี้เป็น service หรือ background process เพื่อจัดการ scheduled jobs

Usage:
    python3 vmreport_scheduler.py
    
    หรือรันเป็น systemd service (แนะนำ)
"""
import psycopg2
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/vmreport_scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('VM Report Scheduler')

# Database connection parameters
DB_HOST = "10.251.150.222"
DB_PORT = "5210"
DB_NAME = "sangfor_scp"
DB_USER = "apirak"
DB_PASS = "Kanokwan@1987#neostar"

def get_db_connection():
    """สร้าง database connection"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def aggregate_daily_stats():
    """Job 1: สร้างสถิติรายวัน (รันทุกวัน 00:30)"""
    try:
        logger.info("Starting daily statistics aggregation...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT vmreport.aggregate_daily_stats()")
        result = cursor.fetchone()
        conn.commit()
        
        if result:
            vms, records = result[0].strip('()').split(',')
            logger.info(f"✓ Daily stats completed: {records} records for {vms} VMs")
        
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"✗ Daily stats failed: {e}")

def calculate_health_scores():
    """Job 2: คำนวณ Health Scores (รันทุก 6 ชั่วโมง)"""
    try:
        logger.info("Starting health score calculation...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
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
        
        rows = cursor.rowcount
        conn.commit()
        logger.info(f"✓ Health scores calculated: {rows} VMs")
        
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"✗ Health score calculation failed: {e}")

def refresh_materialized_view():
    """Job 3: Refresh Materialized View (รันทุก 10 นาที)"""
    try:
        logger.info("Refreshing materialized view...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("REFRESH MATERIALIZED VIEW vmreport.mv_vm_executive_summary")
        conn.commit()
        logger.info("✓ Materialized view refreshed")
        
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"✗ View refresh failed: {e}")

def main():
    logger.info("=" * 60)
    logger.info("VM Resource Intelligence - Background Scheduler Starting")
    logger.info("=" * 60)
    
    scheduler = BlockingScheduler()
    
    # Job 1: Daily stats - ทุกวัน 00:30
    scheduler.add_job(
        aggregate_daily_stats,
        'cron',
        hour=0,
        minute=30,
        id='daily_stats',
        name='Aggregate Daily Statistics'
    )
    logger.info("✓ Scheduled: Daily stats at 00:30")
    
    # Job 2: Health scores - ทุก 6 ชั่วโมง
    scheduler.add_job(
        calculate_health_scores,
        'interval',
        hours=6,
        id='health_scores',
        name='Calculate Health Scores'
    )
    logger.info("✓ Scheduled: Health scores every 6 hours")
    
    # Job 3: Refresh view - ทุก 10 นาที
    scheduler.add_job(
        refresh_materialized_view,
        'interval',
        minutes=10,
        id='refresh_view',
        name='Refresh Materialized View'
    )
    logger.info("✓ Scheduled: View refresh every 10 minutes")
    
    logger.info("=" * 60)
    logger.info("All jobs scheduled successfully!")
    logger.info("Scheduler running... (Press Ctrl+C to exit)")
    logger.info("=" * 60)
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped by user")
        scheduler.shutdown()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Scheduler crashed: {e}")
        sys.exit(1)
