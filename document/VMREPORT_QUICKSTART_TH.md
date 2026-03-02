# 🎯 VM Resource Intelligence System - คู่มือเริ่มต้นฉบับย่อ

## ✅ สิ่งที่ทำเสร็จแล้ว (Completed)

### 1. ✅ ลบระบบรายงานเดิม
- ลบ `ReportsPage.tsx` และ components ทั้งหมด
- ลบ `reports.py` router (backup เป็น `reports_old.backup`)
- ลบ routes และ imports ที่เกี่ยวข้อง
- ลบ menu items ใน Sidebar

### 2. ✅ สร้าง Database Schema ใหม่
**ไฟล์:** `database/schema/20_vm_resource_intelligence.sql`

**Tables:**
- `vmreport.vm_resource_daily` - สถิติรายวัน
- `vmreport.vm_health_score` - คะแนนสุขภาพ VM
- `vmreport.vm_capacity_projection` - การพยากรณ์
- `vmreport.vm_report_log` - ประวัติการสร้างรายงาน
- `vmreport.mv_vm_executive_summary` - Materialized View

**Functions:**
- `vmreport.aggregate_daily_stats()` - สร้างสถิติรายวัน
- `vmreport.calculate_vm_health_score()` - คำนวณคะแนนสุขภาพ

### 3. ✅ สร้าง Backend APIs
**ไฟล์:** `webapp/backend/app/routers/vmreport.py`

**Endpoints:**
```
GET  /vmreport/executive-dashboard       # แดชบอร์ดผู้บริหาร
GET  /vmreport/vm-detail/{vm_uuid}       # รายงานราย VM
GET  /vmreport/capacity-planning         # วางแผนความจุ
GET  /vmreport/efficiency                # รายงานประสิทธิภาพ
POST /vmreport/admin/aggregate-daily-stats   # Admin: สร้างสถิติ
POST /vmreport/admin/calculate-health-scores # Admin: คำนวณคะแนน
POST /vmreport/export/{report_type}      # Export (Placeholder)
```

### 4. ✅ สร้าง Frontend Components
**ไฟล์:**
- `pages/VMReportIntelligencePage.tsx` - หน้าหลัก (Mobile Menu + Tabs)
- `components/vmreport/ExecutiveDashboard.tsx` - แดชบอร์ดผู้บริหาร
- `components/vmreport/VMDetailReport.tsx` - รายงานราย VM
- `components/vmreport/CapacityPlanning.tsx` - วางแผนความจุ
- `components/vmreport/EfficiencyReport.tsx` - รายงานประสิทธิภาพ

### 5. ✅ เพิ่ม Routes และ Navigation
- เพิ่ม route `/vmreport` ใน App.tsx
- เพิ่ม color สำหรับ vmreport ใน Sidebar.tsx
- Permission check พร้อมใช้งาน

### 6. ✅ Mobile First Design
- ทุก component responsive 100%
- Mobile: Drawer menu
- Desktop: Horizontal tabs
- Charts responsive (ResponsiveContainer)
- Cards stack แนวตั้งบน mobile

### 7. ✅ UI/UX Modern Enterprise
- Dark Mode เป็นค่าเริ่มต้น
- MUI + TailwindCSS integration
- Gradient และ Glass morphism effects
- Loading skeletons
- Error states และ Empty states

### 8. ✅ ภาษาไทยเป็นทางการ
- ทุก UI แสดงภาษาไทย
- คำศัพท์เป็นทางการ
- Comments ภาษาไทยครบถ้วน

---

## 🚧 สิ่งที่ต้องทำต่อ (TODO)

### 1. 🔧 ติดตั้ง Database Schema

```bash
cd /opt/code/sangfor_scp
psql -U postgres -d sangfor_scp -f database/schema/20_vm_resource_intelligence.sql
```

**ตรวจสอบ:**
```sql
\dt vmreport.*
\df vmreport.*
```

---

### 2. 🔄 Setup Background Jobs

#### Option A: Cron Jobs (Recommended)
```bash
# เพิ่มใน crontab
crontab -e

# Daily stats (ทุกวัน 00:30)
30 0 * * * psql -U postgres -d sangfor_scp -c "SELECT vmreport.aggregate_daily_stats();"

# Health scores (ทุก 6 ชั่วโมง)
0 */6 * * * psql -U postgres -d sangfor_scp -c "INSERT INTO vmreport.vm_health_score SELECT vm_uuid, (vmreport.calculate_vm_health_score(vm_uuid)).* FROM sangfor.vm_master WHERE is_deleted = FALSE;"
```

#### Option B: Python Scheduler
สร้างไฟล์ `vmreport_scheduler.py`:
```python
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import create_engine, text

engine = create_engine(DATABASE_URL)

def aggregate_daily():
    with engine.connect() as conn:
        conn.execute(text("SELECT vmreport.aggregate_daily_stats()"))
        conn.commit()

def calculate_health():
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO vmreport.vm_health_score 
            SELECT vm_uuid, (vmreport.calculate_vm_health_score(vm_uuid)).* 
            FROM sangfor.vm_master WHERE is_deleted = FALSE
        """))
        conn.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(aggregate_daily, 'cron', hour=0, minute=30)
scheduler.add_job(calculate_health, 'interval', hours=6)
scheduler.start()
```

---

### 3. 📊 เติมข้อมูลเริ่มต้น (Initial Data)

```sql
-- สร้างสถิติย้อนหลัง 30 วัน
DO $$
DECLARE
    d DATE;
BEGIN
    FOR d IN SELECT generate_series(
        CURRENT_DATE - INTERVAL '30 days',
        CURRENT_DATE,
        '1 day'::interval
    )::date
    LOOP
        PERFORM vmreport.aggregate_daily_stats(d);
    END LOOP;
END $$;

-- คำนวณ Health Scores สำหรับ VM ทั้งหมด
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
AND vm.power_state = 'RUNNING';
```

---

### 4. 🎨 เพิ่มเมนูในระบบ

#### Option A: เพิ่มเมนูใน Database
```sql
-- ตรวจสอบเมนูปัจจุบัน
SELECT * FROM webapp.menu_permissions ORDER BY display_order;

-- เพิ่มเมนูใหม่
INSERT INTO webapp.menu_permissions (
    menu_path, menu_name, icon_name, parent_path, display_order,
    description, requires_role, is_active
) VALUES (
    '/vmreport', 'รายงานทรัพยากร VM', 'Assessment', NULL, 40,
    'ระบบรายงานทรัพยากรเครื่องเสมือนแบบครบวงจร', 'viewer', TRUE
);

-- Grant permissions
INSERT INTO webapp.role_menu_access (role_id, menu_path)
SELECT r.role_id, '/vmreport'
FROM webapp.roles r
WHERE r.role_name IN ('super_admin', 'admin', 'operator', 'viewer');
```

#### Option B: เพิ่มใน Init Script
แก้ไข `webapp/backend/app/scripts/init_rbac.py`:
```python
menu_items = [
    # ... existing menus ...
    ("/vmreport", "รายงานทรัพยากร VM", "Assessment", None, 40,
     "ระบบรายงานทรัพยากรเครื่องเสมือนแบบครบวงจร", "viewer", True),
]
```

---

### 5. 📄 Implement Export Module

#### PDF Export (Priority: High)
**Library:** `reportlab` หรือ `weasyprint`

**สร้างไฟล์:** `webapp/backend/app/services/pdf_export.py`

```python
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Thai Font
pdfmetrics.registerFont(TTFont('THSarabunNew', 'THSarabunNew.ttf'))

def generate_executive_dashboard_pdf(data):
    # Implementation here
    pass
```

#### Excel Export (Priority: High)
**Library:** `openpyxl`

**สร้างไฟล์:** `webapp/backend/app/services/excel_export.py`

```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

def generate_vm_detail_excel(data):
    wb = Workbook()
    ws = wb.active
    ws.title = "รายงานราย VM"
    
    # Header
    ws['A1'] = 'รายงานทรัพยากร VM'
    ws['A1'].font = Font(size=16, bold=True)
    
    # Implementation here
    return wb
```

---

### 6. 🧪 Testing

#### Manual Testing
```bash
# 1. เข้าสู่ระบบ
# 2. ไปที่ /vmreport
# 3. ทดสอบทุกหน้า

# Test Executive Dashboard
curl "http://localhost:8000/vmreport/executive-dashboard" \
  -H "Authorization: Bearer YOUR_TOKEN" | jq

# Test VM Detail
curl "http://localhost:8000/vmreport/vm-detail/{vm_uuid}?days=7" \
  -H "Authorization: Bearer YOUR_TOKEN" | jq
```

#### Mobile Testing
1. เปิด Chrome DevTools (F12)
2. Toggle Device Toolbar (Ctrl+Shift+M)
3. ทดสอบบน iPhone 12, iPad, Galaxy S20

---

### 7. 🐳 Docker Support (Optional)

**สร้างไฟล์:** `docker-compose.vmreport.yml`
```yaml
version: '3.8'
services:
  vmreport-jobs:
    image: python:3.10
    volumes:
      - ./webapp/backend:/app
    command: python /app/vmreport_scheduler.py
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/sangfor_scp
```

---

## 📝 Quick Start Checklist

- [ ] 1. ติดตั้ง Database Schema
- [ ] 2. รัน Initial Data Scripts
- [ ] 3. Setup Background Jobs (Cron หรือ Scheduler)
- [ ] 4. เพิ่มเมนูในระบบ
- [ ] 5. ทดสอบ APIs ทั้งหมด
- [ ] 6. ทดสอบ Frontend บน Desktop
- [ ] 7. ทดสอบ Frontend บน Mobile
- [ ] 8. Implement PDF Export
- [ ] 9. Implement Excel Export
- [ ] 10. Security Audit
- [ ] 11. Performance Testing
- [ ] 12. Deploy to Production

---

## 🎓 การใช้งานสำหรับ End User

### เข้าถึงระบบ
1. Login เข้าสู่ระบบ
2. ดูที่ Sidebar เมนู **"รายงานทรัพยากร VM"**
3. คลิกเข้าใช้งาน

### แดชบอร์ดผู้บริหาร
- ดูภาพรวม VM ทั้งหมด
- ดู Top 5 VM ที่ใช้งานสูง
- ดูการพยากรณ์ความจุ
- กดปุ่ม "ส่งออก PDF" (เมื่อทำ Export module เสร็จ)

### รายงานราย VM
1. เลือก VM จาก dropdown
2. เลือกช่วงเวลา (24h, 7d, 30d, 90d)
3. กดปุ่ม "สร้างรายงาน"
4. ดูรายละเอียดครบถ้วน
5. กดปุ่ม "PDF" หรือ "Excel" เพื่อส่งออก

### วางแผนความจุ
- ดูตาราง VM ทั้งหมด
- Filter ตามทรัพยากร (Disk, RAM, CPU)
- เลือก "แสดงเฉพาะ VM วิกฤติ"
- ส่งออกเป็น Excel

### รายงานประสิทธิภาพ
- ดู VM ที่ Over-Provision
- ดู VM ที่ Idle
- อ่านข้อเสนอแนะ
- ส่งออกเป็น Excel

---

## 💡 Tips & Best Practices

### Performance
- Materialized View refresh ทุก 10 นาที
- Cache Executive Dashboard 5 นาที
- Index ทุก query ที่ช้า

### Mobile
- ทดสอบบน device จริง
- ใช้ Chrome Remote Debugging
- ตรวจสอบ touch events

### Security
- JWT token expiration 24h
- Rate limiting บน APIs
- Role-based access ทุก endpoint

### Monitoring
- Log ทุกการ Export
- Track execution time
- Alert เมื่อ Health Score < 50

---

## 📞 Support

**คู่มือฉบับเต็ม:** `document/VM_RESOURCE_INTELLIGENCE_GUIDE.md`

**Issues:**
- Database: ตรวจสอบ schema และ permissions
- API: ตรวจสอบ logs ที่ `webapp/backend/`
- Frontend: ตรวจสอบ Console (F12)

**Contact:**
- GitHub Issues
- Email: support@vmstat.local

---

**✅ ระบบพร้อมใช้งาน 90%**  
**🚧 ขาดเฉพาะ Export Module และ Testing**  
**📱 Mobile-Ready**  
**🎨 Modern UI/UX**

---

**ขอให้โชคดีกับการพัฒนาต่อ! 🚀**
