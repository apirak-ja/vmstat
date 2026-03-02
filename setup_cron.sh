#!/bin/bash
# 
# Cron Jobs Setup for VM Resource Intelligence System
# ติดตั้งคำสั่ง: bash setup_cron.sh
#

echo "=========================================="
echo "VM Resource Intelligence - Cron Jobs Setup"
echo "=========================================="

# Database connection parameters
DB_HOST="10.251.150.222"
DB_PORT="5210"
DB_NAME="sangfor_scp"
DB_USER="apirak"
DB_PASS="Kanokwan@1987#neostar"

# สร้างไฟล์สำหรับ cron jobs
CRON_FILE="/tmp/vmreport_cron.txt"

echo ""
echo "[1/3] Creating cron jobs file..."

cat > "$CRON_FILE" << 'EOF'
# VM Resource Intelligence System - Background Jobs
# 
# 1. Aggregate Daily Stats - รันทุกวันเวลา 00:30
30 0 * * * PGPASSWORD='Kanokwan@1987#neostar' psql -h 10.251.150.222 -p 5210 -U apirak -d sangfor_scp -c "SELECT vmreport.aggregate_daily_stats();" >> /var/log/vmreport_daily.log 2>&1

# 2. Calculate Health Scores - รันทุก 6 ชั่วโมง (00:00, 06:00, 12:00, 18:00)
0 */6 * * * PGPASSWORD='Kanokwan@1987#neostar' psql -h 10.251.150.222 -p 5210 -U apirak -d sangfor_scp -c "INSERT INTO vmreport.vm_health_score (vm_uuid, health_score, risk_level, cpu_score, memory_score, disk_score, network_score, issues, recommendations, is_over_provisioned, is_idle, has_spike) SELECT vm.vm_uuid, (vmreport.calculate_vm_health_score(vm.vm_uuid)).* FROM sangfor.vm_master vm WHERE vm.is_deleted = FALSE;" >> /var/log/vmreport_health.log 2>&1

# 3. Refresh Materialized View - รันทุก 10 นาที
*/10 * * * * PGPASSWORD='Kanokwan@1987#neostar' psql -h 10.251.150.222 -p 5210 -U apirak -d sangfor_scp -c "REFRESH MATERIALIZED VIEW vmreport.mv_vm_executive_summary;" >> /var/log/vmreport_refresh.log 2>&1

EOF

echo "✓ Cron jobs file created: $CRON_FILE"

echo ""
echo "[2/3] Current crontab:"
crontab -l 2>/dev/null || echo "(No crontab currently installed)"

echo ""
echo "[3/3] Installing cron jobs..."
echo ""
echo "Option 1: Install new crontab (replace existing)"
echo "  crontab $CRON_FILE"
echo ""
echo "Option 2: Append to existing crontab"
echo "  (crontab -l 2>/dev/null; cat $CRON_FILE) | crontab -"
echo ""
read -p "Install now? (y/n): " choice

if [ "$choice" = "y" ] || [ "$choice" = "Y" ]; then
    # Append to existing crontab
    (crontab -l 2>/dev/null; cat "$CRON_FILE") | crontab -
    echo "✓ Cron jobs installed successfully"
    echo ""
    echo "New crontab:"
    crontab -l
else
    echo "✗ Installation cancelled"
    echo ""
    echo "Manual installation:"
    echo "  crontab $CRON_FILE"
    echo ""
    echo "Or edit manually:"
    echo "  crontab -e"
fi

echo ""
echo "=========================================="
echo "Log files location:"
echo "  - /var/log/vmreport_daily.log"
echo "  - /var/log/vmreport_health.log"
echo "  - /var/log/vmreport_refresh.log"
echo "=========================================="
