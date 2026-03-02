#!/usr/bin/env python3
"""
Simple Capacity Projection Calculator
คำนวณการเติบโตของทรัพยากร VM จาก daily stats
"""

import sys
import os
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import statistics

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'webapp/backend'))

from app.config import get_settings

settings = get_settings()

# Database connection
DATABASE_URL = f"postgresql://{settings.pgSQL_USERNAME}:{settings.pgSQL_PASSWORD}@{settings.pgSQL_HOST}:{settings.pgSQL_HOST_PORT}/{settings.pgSQL_DBNAME}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def calculate_projections():
    """Calculate capacity projections for all VMs with sufficient data"""
    db = SessionLocal()
    
    try:
        print("🔄 Starting capacity projection calculation...")
        
        # Clear old projections (last 24h)
        print("  Clearing old projections...")
        db.execute(text("""
            DELETE FROM vmreport.vm_capacity_projection
            WHERE projected_at < NOW() - INTERVAL '24 hours'
        """))
        db.commit()
        
        # Get VMs with at least 7 days of data
        vms_query = text("""
            SELECT DISTINCT vm_uuid
            FROM vmreport.vm_resource_daily
            WHERE date >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY vm_uuid
            HAVING COUNT(*) >= 7
        """)
        vm_uuids = [row[0] for row in db.execute(vms_query).fetchall()]
        
        print(f"  Found {len(vm_uuids)} VMs with sufficient data")
        
        if not vm_uuids:
            print("  ⚠️  No VMs with sufficient daily data. Run aggregate_daily_stats first.")
            return 0
        
        inserted = 0
        
        for vm_uuid in vm_uuids:
            # Get daily stats for last 30 days
            stats_query = text("""
                SELECT 
                    date,
                    disk_avg_percent,
                    memory_avg_percent,
                    cpu_avg_percent
                FROM vmreport.vm_resource_daily
                WHERE vm_uuid = :vm_uuid
                AND date >= CURRENT_DATE - INTERVAL '30 days'
                ORDER BY date
            """)
            
            rows = db.execute(stats_query, {"vm_uuid": str(vm_uuid)}).fetchall()
            
            if len(rows) < 7:
                continue
            
            # Calculate for each resource type
            for idx, resource_type in enumerate(['disk', 'memory', 'cpu']):
                values = [row[idx + 1] for row in rows if row[idx + 1] is not None]
                
                if len(values) < 7:
                    continue
                
                # Simple linear regression for growth rate
                # Calculate average daily change
                changes = []
                for i in range(1, len(values)):
                    changes.append(values[i] - values[i-1])
                
                if not changes:
                    continue
                
                avg_change = statistics.mean(changes)
                current_usage = values[-1]
                
                # Calculate days until 80% and 100%
                days_until_80 = None
                days_until_full = None
                estimated_full_date = None
                
                if avg_change > 0.01:  # Growing
                    if current_usage < 80:
                        days_until_80 = int((80 - current_usage) / avg_change)
                    if current_usage < 100:
                        days_until_full = int((100 - current_usage) / avg_change)
                        estimated_full_date = date.today() + timedelta(days=days_until_full)
                
                # Determine confidence level
                std_dev = statistics.stdev(changes) if len(changes) > 1 else 0
                if std_dev < 0.5:
                    confidence = 'สูง'
                elif std_dev < 1.5:
                    confidence = 'ปานกลาง'
                else:
                    confidence = 'ต่ำ'
                
                # Insert projection
                insert_query = text("""
                    INSERT INTO vmreport.vm_capacity_projection (
                        vm_uuid, projection_type, current_usage_percent,
                        growth_rate_per_day, days_until_80_percent, days_until_full,
                        estimated_full_date, confidence_level, based_on_days, forecast_days
                    ) VALUES (
                        :vm_uuid, :projection_type, :current_usage,
                        :growth_rate, :days_80, :days_full,
                        :full_date, :confidence, 30, 90
                    )
                """)
                
                db.execute(insert_query, {
                    "vm_uuid": str(vm_uuid),
                    "projection_type": resource_type,
                    "current_usage": round(current_usage, 2),
                    "growth_rate": round(avg_change, 4),
                    "days_80": days_until_80,
                    "days_full": days_until_full,
                    "full_date": estimated_full_date,
                    "confidence": confidence
                })
                inserted += 1
        
        db.commit()
        print(f"✅ Capacity projections calculated: {inserted} records")
        return inserted
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    count = calculate_projections()
    sys.exit(0 if count > 0 else 1)
