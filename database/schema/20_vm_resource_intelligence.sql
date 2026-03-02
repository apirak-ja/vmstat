-- ==========================================
-- VM Resource Intelligence System - Database Schema
-- ระบบรายงานทรัพยากรเครื่องเสมือนแบบครบวงจร
-- ==========================================

-- Schema: vmreport (ใหม่สำหรับระบบรายงาน)
CREATE SCHEMA IF NOT EXISTS vmreport;

-- ==========================================
-- 1. ตารางสถิติรายวัน (Daily Aggregated Metrics)
-- ==========================================
CREATE TABLE IF NOT EXISTS vmreport.vm_resource_daily (
    id                  BIGSERIAL PRIMARY KEY,
    vm_uuid             UUID NOT NULL,
    date                DATE NOT NULL,
    
    -- CPU Statistics
    cpu_avg_percent     NUMERIC(5,2),
    cpu_max_percent     NUMERIC(5,2),
    cpu_min_percent     NUMERIC(5,2),
    cpu_p95_percent     NUMERIC(5,2),
    
    -- Memory Statistics
    memory_avg_percent  NUMERIC(5,2),
    memory_max_percent  NUMERIC(5,2),
    memory_min_percent  NUMERIC(5,2),
    memory_p95_percent  NUMERIC(5,2),
    memory_avg_mb       BIGINT,
    memory_max_mb       BIGINT,
    
    -- Disk Statistics
    disk_avg_percent    NUMERIC(5,2),
    disk_max_percent    NUMERIC(5,2),
    disk_usage_avg_gb   NUMERIC(12,2),
    disk_usage_max_gb   NUMERIC(12,2),
    
    -- Network Statistics (MB)
    network_in_total_mb NUMERIC(12,2),
    network_out_total_mb NUMERIC(12,2),
    network_in_avg_mbps NUMERIC(10,2),
    network_out_avg_mbps NUMERIC(10,2),
    network_in_max_mbps NUMERIC(10,2),
    network_out_max_mbps NUMERIC(10,2),
    
    -- IOPS Statistics
    iops_read_avg       NUMERIC(10,2),
    iops_write_avg      NUMERIC(10,2),
    iops_read_max       NUMERIC(10,2),
    iops_write_max      NUMERIC(10,2),
    
    -- Metadata
    samples_count       INTEGER DEFAULT 0,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_vm_resource_daily_vm_date UNIQUE (vm_uuid, date)
);

CREATE INDEX IF NOT EXISTS idx_vm_resource_daily_vm ON vmreport.vm_resource_daily(vm_uuid, date DESC);
CREATE INDEX IF NOT EXISTS idx_vm_resource_daily_date ON vmreport.vm_resource_daily(date DESC);

COMMENT ON TABLE vmreport.vm_resource_daily IS 'สถิติการใช้ทรัพยากร VM รายวัน - สำหรับรายงานและกราฟแนวโน้ม';

-- ==========================================
-- 2. ตาราง Health Score และ Risk Assessment
-- ==========================================
CREATE TABLE IF NOT EXISTS vmreport.vm_health_score (
    id                  BIGSERIAL PRIMARY KEY,
    vm_uuid             UUID NOT NULL,
    evaluated_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Overall Health Score (0-100)
    health_score        INTEGER NOT NULL CHECK (health_score >= 0 AND health_score <= 100),
    risk_level          VARCHAR(20) NOT NULL CHECK (risk_level IN ('ปกติ', 'เฝ้าระวัง', 'วิกฤติ')),
    
    -- Component Scores
    cpu_score           INTEGER CHECK (cpu_score >= 0 AND cpu_score <= 100),
    memory_score        INTEGER CHECK (memory_score >= 0 AND memory_score <= 100),
    disk_score          INTEGER CHECK (disk_score >= 0 AND disk_score <= 100),
    network_score       INTEGER CHECK (network_score >= 0 AND network_score <= 100),
    
    -- Issues and Recommendations
    issues              JSONB DEFAULT '[]'::jsonb,
    recommendations     JSONB DEFAULT '[]'::jsonb,
    
    -- Flags
    is_over_provisioned BOOLEAN DEFAULT FALSE,
    is_idle             BOOLEAN DEFAULT FALSE,
    has_spike           BOOLEAN DEFAULT FALSE,
    
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vm_health_vm ON vmreport.vm_health_score(vm_uuid, evaluated_at DESC);
CREATE INDEX IF NOT EXISTS idx_vm_health_risk ON vmreport.vm_health_score(risk_level, health_score);
CREATE INDEX IF NOT EXISTS idx_vm_health_score ON vmreport.vm_health_score(health_score DESC);

COMMENT ON TABLE vmreport.vm_health_score IS 'คะแนนสุขภาพและระดับความเสี่ยงของ VM';

-- ==========================================
-- 3. ตารางการพยากรณ์ทรัพยากร (Capacity Projection)
-- ==========================================
CREATE TABLE IF NOT EXISTS vmreport.vm_capacity_projection (
    id                      BIGSERIAL PRIMARY KEY,
    vm_uuid                 UUID NOT NULL,
    projected_at            TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    projection_type         VARCHAR(20) NOT NULL CHECK (projection_type IN ('disk', 'memory', 'cpu')),
    
    -- Current State
    current_usage_percent   NUMERIC(5,2),
    current_usage_value     NUMERIC(12,2),
    current_capacity        NUMERIC(12,2),
    
    -- Projection Results
    growth_rate_per_day     NUMERIC(10,4),
    days_until_80_percent   INTEGER,
    days_until_full         INTEGER,
    estimated_full_date     DATE,
    
    -- Forecast Data (JSON array of future points)
    forecast_data           JSONB DEFAULT '[]'::jsonb,
    
    -- Confidence
    confidence_level        VARCHAR(20) CHECK (confidence_level IN ('สูง', 'ปานกลาง', 'ต่ำ')),
    model_accuracy          NUMERIC(5,2),
    
    -- Metadata
    based_on_days           INTEGER DEFAULT 30,
    forecast_days           INTEGER DEFAULT 90,
    
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vm_projection_vm ON vmreport.vm_capacity_projection(vm_uuid, projected_at DESC);
CREATE INDEX IF NOT EXISTS idx_vm_projection_type ON vmreport.vm_capacity_projection(projection_type, days_until_full);
CREATE INDEX IF NOT EXISTS idx_vm_projection_critical ON vmreport.vm_capacity_projection(days_until_full) WHERE days_until_full < 30;

COMMENT ON TABLE vmreport.vm_capacity_projection IS 'การพยากรณ์ความจุและการเติบโตของทรัพยากร VM';

-- ==========================================
-- 4. ตารางบันทึกการสร้างรายงาน (Report Generation Log)
-- ==========================================
CREATE TABLE IF NOT EXISTS vmreport.vm_report_log (
    id                  BIGSERIAL PRIMARY KEY,
    report_type         VARCHAR(50) NOT NULL,
    report_name         VARCHAR(200) NOT NULL,
    
    -- Request Parameters
    requested_by_user_id INTEGER,
    requested_by_username VARCHAR(100),
    vm_uuid             UUID,
    date_from           DATE,
    date_to             DATE,
    parameters          JSONB DEFAULT '{}'::jsonb,
    
    -- Execution Info
    status              VARCHAR(20) NOT NULL CHECK (status IN ('success', 'failed', 'processing')),
    execution_time_ms   INTEGER,
    record_count        INTEGER,
    file_format         VARCHAR(10) CHECK (file_format IN ('pdf', 'excel', 'csv')),
    file_size_kb        INTEGER,
    file_path           TEXT,
    
    -- Error Info
    error_message       TEXT,
    
    -- Timestamps
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at        TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_vm_report_log_user ON vmreport.vm_report_log(requested_by_user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_vm_report_log_type ON vmreport.vm_report_log(report_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_vm_report_log_vm ON vmreport.vm_report_log(vm_uuid, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_vm_report_log_status ON vmreport.vm_report_log(status, created_at DESC);

COMMENT ON TABLE vmreport.vm_report_log IS 'บันทึกประวัติการสร้างรายงานทั้งหมด';

-- ==========================================
-- 5. Materialized View: VM Executive Summary
-- ==========================================
CREATE MATERIALIZED VIEW IF NOT EXISTS vmreport.mv_vm_executive_summary AS
SELECT 
    vm.vm_uuid,
    vm.name AS vm_name,
    vm.cpu_cores,
    vm.memory_total_mb,
    vm.storage_total_mb,
    
    -- Latest metrics (last 24h average)
    (
        SELECT AVG(m.cpu_ratio)
        FROM metrics.vm_metrics m
        WHERE m.vm_uuid = vm.vm_uuid 
        AND m.collected_at >= NOW() - INTERVAL '24 hours'
    ) AS cpu_avg_24h,
    
    (
        SELECT AVG(m.memory_ratio)
        FROM metrics.vm_metrics m
        WHERE m.vm_uuid = vm.vm_uuid 
        AND m.collected_at >= NOW() - INTERVAL '24 hours'
    ) AS memory_avg_24h,
    
    (
        SELECT AVG(m.storage_ratio)
        FROM metrics.vm_metrics m
        WHERE m.vm_uuid = vm.vm_uuid 
        AND m.collected_at >= NOW() - INTERVAL '24 hours'
    ) AS disk_avg_24h,
    
    -- Latest health score
    (
        SELECT health_score
        FROM vmreport.vm_health_score h
        WHERE h.vm_uuid = vm.vm_uuid
        ORDER BY h.evaluated_at DESC
        LIMIT 1
    ) AS health_score,
    
    (
        SELECT risk_level
        FROM vmreport.vm_health_score h
        WHERE h.vm_uuid = vm.vm_uuid
        ORDER BY h.evaluated_at DESC
        LIMIT 1
    ) AS risk_level,
    
    COALESCE(lm.power_state, 'unknown') AS power_state,
    vm.is_deleted,
    vm.last_seen_at

FROM sangfor.vm_master vm
LEFT JOIN metrics.vm_latest_metrics lm ON vm.vm_uuid = lm.vm_uuid
WHERE vm.is_deleted = FALSE;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_vm_exec_summary_uuid ON vmreport.mv_vm_executive_summary(vm_uuid);
CREATE INDEX IF NOT EXISTS idx_mv_vm_exec_summary_risk ON vmreport.mv_vm_executive_summary(risk_level);
CREATE INDEX IF NOT EXISTS idx_mv_vm_exec_summary_health ON vmreport.mv_vm_executive_summary(health_score);

COMMENT ON MATERIALIZED VIEW vmreport.mv_vm_executive_summary IS 'สรุปภาพรวม VM สำหรับ Executive Dashboard - Refresh ทุก 10 นาที';

-- ==========================================
-- 6. Function: สร้างสถิติรายวัน (Aggregate Daily Stats)
-- ==========================================
CREATE OR REPLACE FUNCTION vmreport.aggregate_daily_stats(target_date DATE DEFAULT CURRENT_DATE)
RETURNS TABLE(vms_processed INTEGER, records_created INTEGER) AS $$
DECLARE
    v_count INTEGER := 0;
    v_records INTEGER := 0;
BEGIN
    -- Insert/Update daily statistics for all VMs
    INSERT INTO vmreport.vm_resource_daily (
        vm_uuid, date,
        cpu_avg_percent, cpu_max_percent, cpu_min_percent, cpu_p95_percent,
        memory_avg_percent, memory_max_percent, memory_min_percent, memory_p95_percent,
        memory_avg_mb, memory_max_mb,
        disk_avg_percent, disk_max_percent,
        disk_usage_avg_gb, disk_usage_max_gb,
        network_in_total_mb, network_out_total_mb,
        network_in_avg_mbps, network_out_avg_mbps,
        network_in_max_mbps, network_out_max_mbps,
        iops_read_avg, iops_write_avg, iops_read_max, iops_write_max,
        samples_count
    )
    SELECT
        m.vm_uuid,
        target_date,
        
        -- CPU
        AVG(m.cpu_ratio * 100) AS cpu_avg_percent,
        MAX(m.cpu_ratio * 100) AS cpu_max_percent,
        MIN(m.cpu_ratio * 100) AS cpu_min_percent,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY m.cpu_ratio * 100) AS cpu_p95_percent,
        
        -- Memory
        AVG(m.memory_ratio * 100) AS memory_avg_percent,
        MAX(m.memory_ratio * 100) AS memory_max_percent,
        MIN(m.memory_ratio * 100) AS memory_min_percent,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY m.memory_ratio * 100) AS memory_p95_percent,
        AVG(m.memory_used_mb) AS memory_avg_mb,
        MAX(m.memory_used_mb) AS memory_max_mb,
        
        -- Disk
        AVG(m.storage_ratio * 100) AS disk_avg_percent,
        MAX(m.storage_ratio * 100) AS disk_max_percent,
        AVG(m.storage_used_mb / 1024.0) AS disk_usage_avg_gb,
        MAX(m.storage_used_mb / 1024.0) AS disk_usage_max_gb,
        
        -- Network (convert bitps to MB - bitps/8/1024/1024)
        SUM(COALESCE(m.network_read_bitps, 0) / 8.0 / 1024.0 / 1024.0) AS network_in_total_mb,
        SUM(COALESCE(m.network_write_bitps, 0) / 8.0 / 1024.0 / 1024.0) AS network_out_total_mb,
        AVG(COALESCE(m.network_read_bitps, 0) / 8.0 / 1024.0 / 1024.0) AS network_in_avg_mbps,
        AVG(COALESCE(m.network_write_bitps, 0) / 8.0 / 1024.0 / 1024.0) AS network_out_avg_mbps,
        MAX(COALESCE(m.network_read_bitps, 0) / 8.0 / 1024.0 / 1024.0) AS network_in_max_mbps,
        MAX(COALESCE(m.network_write_bitps, 0) / 8.0 / 1024.0 / 1024.0) AS network_out_max_mbps,
        
        -- IOPS
        AVG(COALESCE(m.disk_read_iops, 0)) AS iops_read_avg,
        AVG(COALESCE(m.disk_write_iops, 0)) AS iops_write_avg,
        MAX(COALESCE(m.disk_read_iops, 0)) AS iops_read_max,
        MAX(COALESCE(m.disk_write_iops, 0)) AS iops_write_max,
        
        COUNT(*) AS samples_count
        
    FROM metrics.vm_metrics m
    WHERE DATE(m.collected_at) = target_date
      AND m.power_state = 'on'
    GROUP BY m.vm_uuid
    
    ON CONFLICT (vm_uuid, date) 
    DO UPDATE SET
        cpu_avg_percent = EXCLUDED.cpu_avg_percent,
        cpu_max_percent = EXCLUDED.cpu_max_percent,
        cpu_min_percent = EXCLUDED.cpu_min_percent,
        cpu_p95_percent = EXCLUDED.cpu_p95_percent,
        memory_avg_percent = EXCLUDED.memory_avg_percent,
        memory_max_percent = EXCLUDED.memory_max_percent,
        memory_min_percent = EXCLUDED.memory_min_percent,
        memory_p95_percent = EXCLUDED.memory_p95_percent,
        memory_avg_mb = EXCLUDED.memory_avg_mb,
        memory_max_mb = EXCLUDED.memory_max_mb,
        disk_avg_percent = EXCLUDED.disk_avg_percent,
        disk_max_percent = EXCLUDED.disk_max_percent,
        disk_usage_avg_gb = EXCLUDED.disk_usage_avg_gb,
        disk_usage_max_gb = EXCLUDED.disk_usage_max_gb,
        network_in_total_mb = EXCLUDED.network_in_total_mb,
        network_out_total_mb = EXCLUDED.network_out_total_mb,
        network_in_avg_mbps = EXCLUDED.network_in_avg_mbps,
        network_out_avg_mbps = EXCLUDED.network_out_avg_mbps,
        network_in_max_mbps = EXCLUDED.network_in_max_mbps,
        network_out_max_mbps = EXCLUDED.network_out_max_mbps,
        iops_read_avg = EXCLUDED.iops_read_avg,
        iops_write_avg = EXCLUDED.iops_write_avg,
        iops_read_max = EXCLUDED.iops_read_max,
        iops_write_max = EXCLUDED.iops_write_max,
        samples_count = EXCLUDED.samples_count;
    
    GET DIAGNOSTICS v_records = ROW_COUNT;
    
    -- Count unique VMs
    SELECT COUNT(DISTINCT vm_uuid) INTO v_count
    FROM vmreport.vm_resource_daily
    WHERE date = target_date;
    
    RETURN QUERY SELECT v_count, v_records;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION vmreport.aggregate_daily_stats IS 'สร้างสถิติรายวันจาก vm_metrics - เรียกใช้ทุกวันเวลา 00:30';

-- ==========================================
-- 7. Function: คำนวณ Health Score
-- ==========================================
CREATE OR REPLACE FUNCTION vmreport.calculate_vm_health_score(p_vm_uuid UUID)
RETURNS TABLE(
    health_score INTEGER,
    risk_level VARCHAR(20),
    cpu_score INTEGER,
    memory_score INTEGER,
    disk_score INTEGER,
    network_score INTEGER,
    issues JSONB,
    recommendations JSONB,
    is_over_provisioned BOOLEAN,
    is_idle BOOLEAN,
    has_spike BOOLEAN
) AS $$
DECLARE
    v_cpu_avg NUMERIC;
    v_memory_avg NUMERIC;
    v_disk_avg NUMERIC;
    v_cpu_max NUMERIC;
    v_memory_max NUMERIC;
    v_disk_max NUMERIC;
    v_cpu_score INTEGER;
    v_memory_score INTEGER;
    v_disk_score INTEGER;
    v_network_score INTEGER := 100;
    v_health_score INTEGER;
    v_risk_level VARCHAR(20);
    v_issues JSONB := '[]'::jsonb;
    v_recommendations JSONB := '[]'::jsonb;
    v_is_over_provisioned BOOLEAN := FALSE;
    v_is_idle BOOLEAN := FALSE;
    v_has_spike BOOLEAN := FALSE;
BEGIN
    -- ดึงข้อมูลย้อนหลัง 7 วัน
    SELECT 
        AVG(cpu_avg_percent),
        AVG(memory_avg_percent),
        AVG(disk_avg_percent),
        MAX(cpu_max_percent),
        MAX(memory_max_percent),
        MAX(disk_max_percent)
    INTO v_cpu_avg, v_memory_avg, v_disk_avg, v_cpu_max, v_memory_max, v_disk_max
    FROM vmreport.vm_resource_daily
    WHERE vm_uuid = p_vm_uuid
      AND date >= CURRENT_DATE - INTERVAL '7 days';
    
    -- ถ้าไม่มีข้อมูล ให้คะแนนเต็ม
    IF v_cpu_avg IS NULL THEN
        RETURN QUERY SELECT 100, 'ปกติ'::VARCHAR(20), 100, 100, 100, 100, 
                     '[]'::jsonb, '[]'::jsonb, FALSE, FALSE, FALSE;
        RETURN;
    END IF;
    
    -- คำนวณคะแนน CPU (0-100, ยิ่งใช้น้อยยิ่งดี แต่ idle มากเกินไปก็ไม่ดี)
    IF v_cpu_avg < 5 THEN
        v_cpu_score := 70; -- Idle
        v_is_idle := TRUE;
        v_issues := v_issues || '["CPU ใช้งานต่ำมาก"]'::jsonb;
        v_recommendations := v_recommendations || '["พิจารณาลดจำนวน vCPU"]'::jsonb;
    ELSIF v_cpu_avg < 30 THEN
        v_cpu_score := 100; -- Optimal
    ELSIF v_cpu_avg < 60 THEN
        v_cpu_score := 90; -- Good
    ELSIF v_cpu_avg < 80 THEN
        v_cpu_score := 60; -- Warning
        v_issues := v_issues || '["CPU ใช้งานสูง"]'::jsonb;
        v_recommendations := v_recommendations || '["พิจารณาเพิ่ม vCPU หรือตรวจสอบ process"]'::jsonb;
    ELSE
        v_cpu_score := 30; -- Critical
        v_issues := v_issues || '["CPU ใช้งานสูงมาก"]'::jsonb;
        v_recommendations := v_recommendations || '["เพิ่ม vCPU โดยเร็ว"]'::jsonb;
    END IF;
    
    -- คำนวณคะแนน Memory
    IF v_memory_avg < 10 THEN
        v_memory_score := 70; -- Under-utilized
        v_is_over_provisioned := TRUE;
        v_issues := v_issues || '["RAM ใช้งานต่ำมาก"]'::jsonb;
        v_recommendations := v_recommendations || '["พิจารณาลดขนาด RAM"]'::jsonb;
    ELSIF v_memory_avg < 70 THEN
        v_memory_score := 100; -- Optimal
    ELSIF v_memory_avg < 85 THEN
        v_memory_score := 70; -- Warning
        v_issues := v_issues || '["RAM ใช้งานสูง"]'::jsonb;
        v_recommendations := v_recommendations || '["พิจารณาเพิ่ม RAM"]'::jsonb;
    ELSE
        v_memory_score := 30; -- Critical
        v_issues := v_issues || '["RAM ใช้งานวิกฤติ"]'::jsonb;
        v_recommendations := v_recommendations || '["เพิ่ม RAM โดยทันที"]'::jsonb;
    END IF;
    
    -- คำนวณคะแนน Disk
    IF v_disk_avg < 50 THEN
        v_disk_score := 100; -- Good
    ELSIF v_disk_avg < 75 THEN
        v_disk_score := 80; -- OK
    ELSIF v_disk_avg < 90 THEN
        v_disk_score := 50; -- Warning
        v_issues := v_issues || '["พื้นที่ดิสก์ใกล้เต็ม"]'::jsonb;
        v_recommendations := v_recommendations || '["เพิ่มพื้นที่ดิสก์หรือลบไฟล์ไม่จำเป็น"]'::jsonb;
    ELSE
        v_disk_score := 20; -- Critical
        v_issues := v_issues || '["พื้นที่ดิสก์เต็มเกือบหมด"]'::jsonb;
        v_recommendations := v_recommendations || '["เพิ่มพื้นที่ดิสก์โดยเร็ว"]'::jsonb;
    END IF;
    
    -- ตรวจสอบ Spike
    IF v_cpu_max > 95 OR v_memory_max > 95 THEN
        v_has_spike := TRUE;
        v_issues := v_issues || '["มีการใช้ทรัพยากรสูงกะทันหัน (Spike)"]'::jsonb;
        v_recommendations := v_recommendations || '["ตรวจสอบ logs และ process ที่ทำให้เกิด spike"]'::jsonb;
    END IF;
    
    -- คำนวณคะแนนรวม (weighted average)
    v_health_score := (v_cpu_score * 30 + v_memory_score * 30 + v_disk_score * 30 + v_network_score * 10) / 100;
    
    -- กำหนด Risk Level
    IF v_health_score >= 80 THEN
        v_risk_level := 'ปกติ';
    ELSIF v_health_score >= 50 THEN
        v_risk_level := 'เฝ้าระวัง';
    ELSE
        v_risk_level := 'วิกฤติ';
    END IF;
    
    RETURN QUERY SELECT 
        v_health_score,
        v_risk_level,
        v_cpu_score,
        v_memory_score,
        v_disk_score,
        v_network_score,
        v_issues,
        v_recommendations,
        v_is_over_provisioned,
        v_is_idle,
        v_has_spike;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION vmreport.calculate_vm_health_score IS 'คำนวณคะแนนสุขภาพและความเสี่ยงของ VM';

-- ==========================================
-- 8. Permissions
-- ==========================================
GRANT USAGE ON SCHEMA vmreport TO PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA vmreport TO PUBLIC;
GRANT SELECT ON vmreport.mv_vm_executive_summary TO PUBLIC;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA vmreport TO PUBLIC;

-- ==========================================
-- เสร็จสิ้น! 🎉
-- ==========================================
