"""
VM Resource Intelligence System - Backend API
ระบบรายงานทรัพยากรเครื่องเสมือน (VM Resource Intelligence System)

รองรับ:
- Executive Dashboard
- Per-VM Detail Report
- Capacity Planning Report
- Efficiency Report
- Export PDF และ Excel
"""
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, date
from pydantic import BaseModel
import json

from ..database import get_db
from ..utils.auth import get_current_user

router = APIRouter(prefix="/vmreport", tags=["VM Resource Intelligence"])


# ==========================================
# Pydantic Models
# ==========================================

class VMBasicInfo(BaseModel):
    vm_uuid: str
    vm_name: str
    cluster_name: Optional[str]
    host_name: Optional[str]
    ip_address: Optional[str]
    vcpu: int
    vram_mb: int
    disk_total_gb: float
    power_state: str


class VMSnapshot(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_in_mbps: float
    network_out_mbps: float


class VMStatistics(BaseModel):
    metric: str
    avg: float
    max: float
    min: float
    p95: Optional[float]


class HealthScore(BaseModel):
    score: int
    risk_level: str
    cpu_score: int
    memory_score: int
    disk_score: int
    issues: List[str]
    recommendations: List[str]


class CapacityProjection(BaseModel):
    resource_type: str
    current_usage: float
    growth_rate: float
    days_until_80: Optional[int]
    days_until_full: Optional[int]
    estimated_full_date: Optional[str]


# ==========================================
# 1. Executive Dashboard API
# ==========================================

@router.get("/executive-dashboard")
async def get_executive_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    📊 Executive Dashboard - สรุปภาพรวมทรัพยากร VM ทั้งหมด
    
    Returns:
    - จำนวน VM ทั้งหมด
    - VM ที่มีความเสี่ยงสูง (วิกฤติ, เฝ้าระวัง)
    - กราฟภาพรวม CPU/RAM/Disk
    - Top 5 VM ที่ใช้ทรัพยากรสูงสุด
    - Capacity Forecast
    """
    
    # 1. จำนวน VM ทั้งหมด (นับทุก VM ที่ไม่ลบ ไม่เฉพาะที่เปิดอยู่)
    total_vms_query = text("""
        SELECT COUNT(*) as total
        FROM sangfor.vm_master
        WHERE is_deleted = FALSE
    """)
    total_vms = db.execute(total_vms_query).fetchone()[0]
    
    # 2. VM ที่มีความเสี่ยง
    risk_vms_query = text("""
        SELECT 
            risk_level,
            COUNT(*) as count
        FROM vmreport.vm_health_score h
        WHERE h.evaluated_at >= NOW() - INTERVAL '24 hours'
        GROUP BY risk_level
    """)
    risk_breakdown = {row[0]: row[1] for row in db.execute(risk_vms_query).fetchall()}
    
    critical_vms = risk_breakdown.get('วิกฤติ', 0)
    warning_vms = risk_breakdown.get('เฝ้าระวัง', 0)
    
    # 3. กราฟภาพรวม (เฉลี่ย 7 วันล่าสุด)
    overview_query = text("""
        SELECT 
            date,
            AVG(cpu_avg_percent) as cpu_avg,
            AVG(memory_avg_percent) as memory_avg,
            AVG(disk_avg_percent) as disk_avg
        FROM vmreport.vm_resource_daily
        WHERE date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY date
        ORDER BY date
    """)
    overview_data = [
        {
            "date": str(row[0]),
            "cpu": float(row[1]) if row[1] else 0,
            "memory": float(row[2]) if row[2] else 0,
            "disk": float(row[3]) if row[3] else 0
        }
        for row in db.execute(overview_query).fetchall()
    ]
    
    # 4. Top 5 VM ที่ใช้งานสูงสุด (CPU)
    top_cpu_query = text("""
        SELECT 
            vm.name,
            d.cpu_avg_percent,
            d.memory_avg_percent,
            d.disk_avg_percent
        FROM vmreport.vm_resource_daily d
        JOIN sangfor.vm_master vm ON d.vm_uuid = vm.vm_uuid
        WHERE d.date = CURRENT_DATE - INTERVAL '1 day'
        ORDER BY d.cpu_avg_percent DESC
        LIMIT 5
    """)
    top_vms = [
        {
            "vm_name": row[0],
            "cpu_percent": float(row[1]) if row[1] else 0,
            "memory_percent": float(row[2]) if row[2] else 0,
            "disk_percent": float(row[3]) if row[3] else 0
        }
        for row in db.execute(top_cpu_query).fetchall()
    ]
    
    # 5. Capacity Forecast Summary
    forecast_query = text("""
        SELECT 
            projection_type,
            AVG(days_until_full) as avg_days_until_full,
            COUNT(*) FILTER (WHERE days_until_full < 30) as critical_count
        FROM vmreport.vm_capacity_projection
        WHERE projected_at >= NOW() - INTERVAL '24 hours'
        AND days_until_full IS NOT NULL
        GROUP BY projection_type
    """)
    forecast_data = [
        {
            "resource": row[0],
            "avg_days_until_full": int(row[1]) if row[1] else None,
            "critical_count": row[2]
        }
        for row in db.execute(forecast_query).fetchall()
    ]
    
    return {
        "success": True,
        "data": {
            "summary": {
                "total_vms": total_vms,
                "critical_vms": critical_vms,
                "warning_vms": warning_vms,
                "healthy_vms": total_vms - critical_vms - warning_vms
            },
            "overview_chart": overview_data,
            "top_vms": top_vms,
            "capacity_forecast": forecast_data
        }
    }


# ==========================================
# 2. Per-VM Detail Report API
# ==========================================

@router.get("/vm-detail/{vm_uuid}")
async def get_vm_detail_report(
    vm_uuid: str,
    days: int = Query(7, ge=1, le=90, description="จำนวนวันย้อนหลัง"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    📄 Per-VM Detail Report - รายงานรายละเอียดของ VM แต่ละตัว
    
    Sections:
    1. ข้อมูลพื้นฐาน
    2. Snapshot ปัจจุบัน
    3. กราฟย้อนหลัง (days)
    4. ตารางสถิติ
    5. วิเคราะห์แนวโน้ม
    """
    
    # 1. ข้อมูลพื้นฐาน
    basic_info_query = text("""
        SELECT 
            vm.vm_uuid,
            vm.name,
            g.group_name as cluster_name,
            h.host_name,
            vm.ip_address,
            vm.cpu_cores,
            vm.memory_total_mb,
            vm.storage_total_mb,
            vm.power_state
        FROM sangfor.vm_master vm
        LEFT JOIN sangfor.vm_group_master g ON vm.group_id = g.group_id
        LEFT JOIN sangfor.host_master h ON vm.host_id = h.host_id
        WHERE vm.vm_uuid = CAST(:vm_uuid AS uuid)
    """)
    basic_row = db.execute(basic_info_query, {"vm_uuid": vm_uuid}).fetchone()
    
    if not basic_row:
        raise HTTPException(status_code=404, detail="VM not found")
    
    basic_info = {
        "vm_uuid": str(basic_row[0]),
        "vm_name": basic_row[1],
        "cluster_name": basic_row[2],
        "host_name": basic_row[3],
        "ip_address": basic_row[4],
        "vcpu": basic_row[5],
        "vram_mb": basic_row[6],
        "disk_total_gb": round(basic_row[7] / 1024.0, 2) if basic_row[7] else 0,
        "power_state": basic_row[8]
    }
    
    # 2. Snapshot ปัจจุบัน (ข้อมูลล่าสุดภายใน 10 นาที)
    snapshot_query = text("""
        SELECT 
            cpu_ratio * 100 as cpu_percent,
            memory_ratio * 100 as memory_percent,
            storage_ratio * 100 as disk_percent,
            COALESCE(network_in_bytes, 0) / 1024.0 / 1024.0 as network_in_mbps,
            COALESCE(network_out_bytes, 0) / 1024.0 / 1024.0 as network_out_mbps
        FROM metrics.vm_metrics
        WHERE vm_uuid = CAST(:vm_uuid AS uuid)
        AND collected_at >= NOW() - INTERVAL '10 minutes'
        ORDER BY collected_at DESC
        LIMIT 1
    """)
    snapshot_row = db.execute(snapshot_query, {"vm_uuid": vm_uuid}).fetchone()
    
    snapshot = {
        "cpu_percent": round(snapshot_row[0], 2) if snapshot_row and snapshot_row[0] else 0,
        "memory_percent": round(snapshot_row[1], 2) if snapshot_row and snapshot_row[1] else 0,
        "disk_percent": round(snapshot_row[2], 2) if snapshot_row and snapshot_row[2] else 0,
        "network_in_mbps": round(snapshot_row[3], 2) if snapshot_row and snapshot_row[3] else 0,
        "network_out_mbps": round(snapshot_row[4], 2) if snapshot_row and snapshot_row[4] else 0
    }
    
    # 3. กราฟย้อนหลัง (รายวัน)
    historical_query = text("""
        SELECT 
            date,
            cpu_avg_percent,
            cpu_max_percent,
            memory_avg_percent,
            memory_max_percent,
            disk_avg_percent,
            network_in_total_mb,
            network_out_total_mb,
            iops_read_avg,
            iops_write_avg
        FROM vmreport.vm_resource_daily
        WHERE vm_uuid = CAST(:vm_uuid AS uuid)
        AND date >= CURRENT_DATE - CAST(:days || ' days' AS INTERVAL)
        ORDER BY date
    """)
    historical_data = [
        {
            "date": str(row[0]),
            "cpu_avg": round(float(row[1]), 2) if row[1] else 0,
            "cpu_max": round(float(row[2]), 2) if row[2] else 0,
            "memory_avg": round(float(row[3]), 2) if row[3] else 0,
            "memory_max": round(float(row[4]), 2) if row[4] else 0,
            "disk_avg": round(float(row[5]), 2) if row[5] else 0,
            "network_in_mb": round(float(row[6]), 2) if row[6] else 0,
            "network_out_mb": round(float(row[7]), 2) if row[7] else 0,
            "iops_read": round(float(row[8]), 2) if row[8] else 0,
            "iops_write": round(float(row[9]), 2) if row[9] else 0
        }
        for row in db.execute(historical_query, {"vm_uuid": vm_uuid, "days": days}).fetchall()
    ]
    
    # 4. ตารางสถิติ
    stats_query = text("""
        SELECT 
            'CPU' as metric,
            cpu_avg_percent as avg,
            cpu_max_percent as max,
            cpu_min_percent as min,
            cpu_p95_percent as p95
        FROM vmreport.vm_resource_daily
        WHERE vm_uuid = CAST(:vm_uuid AS uuid)
        AND date >= CURRENT_DATE - CAST(:days || ' days' AS INTERVAL)
        HAVING COUNT(*) > 0
        
        UNION ALL
        
        SELECT 
            'Memory',
            AVG(memory_avg_percent),
            MAX(memory_max_percent),
            MIN(memory_min_percent),
            AVG(memory_p95_percent)
        FROM vmreport.vm_resource_daily
        WHERE vm_uuid = CAST(:vm_uuid AS uuid)
        AND date >= CURRENT_DATE - CAST(:days || ' days' AS INTERVAL)
        HAVING COUNT(*) > 0
        
        UNION ALL
        
        SELECT 
            'Disk',
            AVG(disk_avg_percent),
            MAX(disk_max_percent),
            NULL,
            NULL
        FROM vmreport.vm_resource_daily
        WHERE vm_uuid = CAST(:vm_uuid AS uuid)
        AND date >= CURRENT_DATE - CAST(:days || ' days' AS INTERVAL)
        HAVING COUNT(*) > 0
    """)
    statistics = [
        {
            "metric": row[0],
            "avg": round(float(row[1]), 2) if row[1] else 0,
            "max": round(float(row[2]), 2) if row[2] else 0,
            "min": round(float(row[3]), 2) if row[3] else 0,
            "p95": round(float(row[4]), 2) if row[4] else None
        }
        for row in db.execute(stats_query, {"vm_uuid": vm_uuid, "days": days}).fetchall()
    ]
    
    # 5. Health Score & Trend Analysis
    health_query = text("""
        SELECT 
            health_score,
            risk_level,
            cpu_score,
            memory_score,
            disk_score,
            issues,
            recommendations,
            is_over_provisioned,
            is_idle,
            has_spike
        FROM vmreport.vm_health_score
        WHERE vm_uuid = CAST(:vm_uuid AS uuid)
        ORDER BY evaluated_at DESC
        LIMIT 1
    """)
    health_row = db.execute(health_query, {"vm_uuid": vm_uuid}).fetchone()
    
    health_analysis = None
    if health_row:
        health_analysis = {
            "score": health_row[0],
            "risk_level": health_row[1],
            "cpu_score": health_row[2],
            "memory_score": health_row[3],
            "disk_score": health_row[4],
            "issues": health_row[5] if health_row[5] else [],
            "recommendations": health_row[6] if health_row[6] else [],
            "is_over_provisioned": health_row[7],
            "is_idle": health_row[8],
            "has_spike": health_row[9]
        }
    
    # Capacity Projection
    projection_query = text("""
        SELECT 
            projection_type,
            current_usage_percent,
            growth_rate_per_day,
            days_until_80_percent,
            days_until_full,
            estimated_full_date,
            confidence_level
        FROM vmreport.vm_capacity_projection
        WHERE vm_uuid = CAST(:vm_uuid AS uuid)
        AND projected_at >= NOW() - INTERVAL '24 hours'
        ORDER BY projected_at DESC
        LIMIT 3
    """)
    projections = [
        {
            "resource_type": row[0],
            "current_usage": round(float(row[1]), 2) if row[1] else 0,
            "growth_rate": round(float(row[2]), 4) if row[2] else 0,
            "days_until_80": row[3],
            "days_until_full": row[4],
            "estimated_full_date": str(row[5]) if row[5] else None,
            "confidence": row[6]
        }
        for row in db.execute(projection_query, {"vm_uuid": vm_uuid}).fetchall()
    ]
    
    return {
        "success": True,
        "data": {
            "basic_info": basic_info,
            "snapshot": snapshot,
            "historical_data": historical_data,
            "statistics": statistics,
            "health_analysis": health_analysis,
            "capacity_projections": projections
        }
    }


# ==========================================
# 3. Capacity Planning Report API
# ==========================================

@router.get("/capacity-planning")
async def get_capacity_planning_report(
    resource_type: Optional[str] = Query(None, description="disk, memory, cpu"),
    critical_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    📈 Capacity Planning Report - รายงานการวางแผนความจุ
    
    แสดง:
    - แนวโน้มการเติบโต
    - วันที่คาดว่าจะเต็ม
    - ตาราง Forecast
    """
    
    query = text("""
        SELECT 
            vm.name as vm_name,
            p.projection_type,
            p.current_usage_percent,
            p.growth_rate_per_day,
            p.days_until_full,
            p.estimated_full_date,
            p.confidence_level,
            vm.cpu_cores,
            vm.memory_total_mb,
            vm.storage_total_mb
        FROM vmreport.vm_capacity_projection p
        JOIN sangfor.vm_master vm ON p.vm_uuid = vm.vm_uuid
        WHERE p.projected_at >= NOW() - INTERVAL '24 hours'
        """ + (
            " AND p.projection_type = :resource_type" if resource_type else ""
        ) + (
            " AND p.days_until_full < 30" if critical_only else ""
        ) + """
        ORDER BY p.days_until_full ASC NULLS LAST, vm.name
    """)
    
    params = {}
    if resource_type:
        params["resource_type"] = resource_type
    
    results = db.execute(query, params).fetchall()
    
    data = [
        {
            "vm_name": row[0],
            "resource_type": row[1],
            "current_usage_percent": round(float(row[2]), 2) if row[2] else 0,
            "growth_rate_per_day": round(float(row[3]), 4) if row[3] else 0,
            "days_until_full": row[4],
            "estimated_full_date": str(row[5]) if row[5] else None,
            "confidence_level": row[6],
            "vcpu": row[7],
            "vram_mb": row[8],
            "disk_total_mb": row[9]
        }
        for row in results
    ]
    
    return {
        "success": True,
        "data": data,
        "total_count": len(data)
    }


# ==========================================
# 4. Efficiency Report API
# ==========================================

@router.get("/efficiency")
async def get_efficiency_report(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    ⚡ Efficiency Report - รายงานประสิทธิภาพ
    
    วิเคราะห์:
    - VM ที่ Over-Provision
    - VM ที่ Idle
    - ข้อเสนอแนะลด Resource
    """
    
    query = text("""
        SELECT 
            vm.name as vm_name,
            vm.cpu_cores,
            vm.memory_total_mb,
            vm.storage_total_mb,
            h.health_score,
            h.risk_level,
            h.is_over_provisioned,
            h.is_idle,
            d.cpu_avg_percent,
            d.memory_avg_percent,
            d.disk_avg_percent,
            h.recommendations
        FROM vmreport.vm_health_score h
        JOIN sangfor.vm_master vm ON h.vm_uuid = vm.vm_uuid
        LEFT JOIN vmreport.vm_resource_daily d ON h.vm_uuid = d.vm_uuid 
            AND d.date = CURRENT_DATE - INTERVAL '1 day'
        WHERE h.evaluated_at >= NOW() - INTERVAL '24 hours'
        AND (h.is_over_provisioned = TRUE OR h.is_idle = TRUE)
        ORDER BY h.health_score ASC, vm.name
    """)
    
    results = db.execute(query).fetchall()
    
    data = [
        {
            "vm_name": row[0],
            "vcpu": row[1],
            "vram_mb": row[2],
            "disk_total_mb": row[3],
            "health_score": row[4],
            "risk_level": row[5],
            "is_over_provisioned": row[6],
            "is_idle": row[7],
            "cpu_avg_percent": round(float(row[8]), 2) if row[8] else 0,
            "memory_avg_percent": round(float(row[9]), 2) if row[9] else 0,
            "disk_avg_percent": round(float(row[10]), 2) if row[10] else 0,
            "recommendations": row[11] if row[11] else []
        }
        for row in results
    ]
    
    return {
        "success": True,
        "data": data,
        "total_count": len(data),
        "summary": {
            "over_provisioned_count": sum(1 for d in data if d["is_over_provisioned"]),
            "idle_count": sum(1 for d in data if d["is_idle"])
        }
    }


# ==========================================
# 5. Background Job: Update Daily Stats
# ==========================================

@router.post("/admin/aggregate-daily-stats")
async def trigger_daily_aggregation(
    target_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🔄 Trigger Daily Stats Aggregation (Admin Only)
    """
    
    # Check admin permission
    if current_user.get("role_level", 0) < 80:
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    date_param = target_date if target_date else "CURRENT_DATE"
    
    query = text(f"""
        SELECT * FROM vmreport.aggregate_daily_stats({date_param})
    """)
    
    result = db.execute(query).fetchone()
    db.commit()
    
    return {
        "success": True,
        "message": "Daily stats aggregated successfully",
        "vms_processed": result[0],
        "records_created": result[1]
    }


# ==========================================
# 6. Background Job: Calculate Health Scores
# ==========================================

@router.post("/admin/calculate-health-scores")
async def trigger_health_score_calculation(
    vm_uuid: Optional[str] = Query(None, description="Specific VM UUID or all if null"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🏥 Calculate Health Scores (Admin Only)
    """
    
    # Check admin permission
    if current_user.get("role_level", 0) < 80:
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    if vm_uuid:
        # Calculate for specific VM
        query = text("""
            INSERT INTO vmreport.vm_health_score (
                vm_uuid, health_score, risk_level, cpu_score, memory_score, 
                disk_score, network_score, issues, recommendations,
                is_over_provisioned, is_idle, has_spike
            )
            SELECT 
                CAST(:vm_uuid AS uuid),
                (vmreport.calculate_vm_health_score(CAST(:vm_uuid AS uuid))).*
        """)
        db.execute(query, {"vm_uuid": vm_uuid})
        count = 1
    else:
        # Calculate for all VMs
        query = text("""
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
            AND vm.power_state = 'RUNNING'
        """)
        result = db.execute(query)
        count = result.rowcount
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Health scores calculated for {count} VMs",
        "count": count
    }


# ==========================================
# 6b. Background Job: Calculate Capacity Projections
# ==========================================

@router.post("/admin/calculate-capacity-projections")
async def trigger_capacity_projection(
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🔮 Calculate Capacity Projections (Admin Only)
    
    คำนวณการเติบโตของทรัพยากร VM จาก daily statsและพยากรณ์วันที่จะเต็ม
    """
    
    import statistics
    from datetime import date, timedelta
    
    # Clear old projections
    db.execute(text("DELETE FROM vmreport.vm_capacity_projection WHERE projected_at < NOW() - INTERVAL '24 hours'"))
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
    
    if not vm_uuids:
        return {
            "success": False,
            "message": "No VMs with sufficient daily data. Run aggregate-daily-stats first.",
            "count": 0
        }
    
    inserted = 0
    
    for vm_uuid in vm_uuids:
        # Get daily stats
        stats_query = text("""
            SELECT date, disk_avg_percent, memory_avg_percent, cpu_avg_percent
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
            values = [float(row[idx + 1]) for row in rows if row[idx + 1] is not None]
            
            if len(values) < 7:
                continue
            
            # Calculate average daily change
            changes = [values[i] - values[i-1] for i in range(1, len(values))]
            
            if not changes:
                continue
            
            avg_change = statistics.mean(changes)
            current_usage = values[-1]
            
            # Calculate days until thresholds
            days_until_80 = None
            days_until_full = None
            estimated_full_date = None
            
            if avg_change > 0.01:  # Growing
                if current_usage < 80:
                    days_until_80 = int((80 - current_usage) / avg_change)
                if current_usage < 100:
                    days_until_full = int((100 - current_usage) / avg_change)
                    estimated_full_date = date.today() + timedelta(days=days_until_full)
            
            # Confidence based on standard deviation
            std_dev = statistics.stdev(changes) if len(changes) > 1 else 0
            confidence = 'สูง' if std_dev < 0.5 else ('ปานกลาง' if std_dev < 1.5 else 'ต่ำ')
            
            # Insert projection
            insert_query = text("""
                INSERT INTO vmreport.vm_capacity_projection (
                    vm_uuid, projection_type, current_usage_percent,
                    growth_rate_per_day, days_until_80_percent, days_until_full,
                    estimated_full_date, confidence_level, based_on_days, forecast_days
                ) VALUES (
                    CAST(:vm_uuid AS uuid), :projection_type, :current_usage,
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
    
    return {
        "success": True,
        "message": f"Capacity projections calculated for {len(vm_uuids)} VMs",
        "count": inserted,
        "vms_processed": len(vm_uuids)
    }


# ==========================================
# 7. Export Helper (สำหรับ PDF/Excel - ใช้ในขั้นตอนต่อไป)
# ==========================================

@router.post("/export/{report_type}")
async def export_report(
    report_type: str,
    format: str = Query("pdf", description="pdf or excel"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    📥 Export Report (Placeholder - จะทำใน export module)
    """
    
    # Log the export request
    log_query = text("""
        INSERT INTO vmreport.vm_report_log (
            report_type, report_name, requested_by_user_id, 
            requested_by_username, file_format, status
        )
        VALUES (
            :report_type, :report_name, :user_id,
            :username, :format, 'processing'
        )
        RETURNING id
    """)
    
    result = db.execute(log_query, {
        "report_type": report_type,
        "report_name": f"รายงาน{report_type}",
        "user_id": current_user.get("user_id"),
        "username": current_user.get("username"),
        "format": format
    })
    log_id = result.fetchone()[0]
    db.commit()
    
    return {
        "success": True,
        "message": "Export request received",
        "log_id": log_id,
        "note": "Export module will be implemented in next step"
    }
