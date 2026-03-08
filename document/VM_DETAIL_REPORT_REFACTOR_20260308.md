# VM Detail Report Refactor (2026-03-08)

## Scope
ปรับปรุงหน้า VM Detail ตามข้อกำหนด:
1. ย้ายปุ่มออกรายงานไปอยู่ในส่วน Session hero
2. ลบแท็บรายงานออก
3. ปรับรูปแบบรายงานให้ดูเป็นมืออาชีพและเหมาะกับการพิมพ์
4. ทดสอบการเปลี่ยนแปลงและ cleanup โค้ดที่ไม่เกี่ยวข้อง
5. ทดสอบ `start.sh`

## Files Changed
- `webapp/frontend/src/pages/VMDetailPage.tsx`
- `webapp/frontend/src/pages/vmdetail/tabs/Tab7Report.tsx`

## Implementation Details

### 1) Move Report Action to Session Hero
- เพิ่มปุ่ม `ออกรายงาน` ในส่วน Action Buttons ของ Session hero
- ดีไซน์ปุ่มให้กลมกลืนกับ hero (gradient + shadow + responsive)
- เมื่อกดปุ่ม:
  - เปิดส่วนรายงานผ่าน state `showReport`
  - auto scroll ไปยัง section รายงาน (`#vm-detail-report-section`)

### 2) Remove Report Tab
- ลบแท็บ `รายงาน` ออกจาก Tabs navigation
- ปรับลำดับแท็บให้ `Raw Data` ขยับมาเป็น index 7
- ปรับ logic query/raw tab condition ตาม index ใหม่

### 3) Keep Report Available Without Tab
- ย้ายการ render รายงานให้เป็น section ภายนอก tabs card
- ควบคุมการแสดงผลด้วย `showReport`
- ปรับเงื่อนไขการโหลดข้อมูลที่รายงานใช้ (metrics/realtime/disks/networks/alarms)
  ให้โหลดเมื่อ `showReport` เปิดใช้งาน แม้ไม่ได้อยู่ในแท็บเดิม

### 4) Professional Report Styling
- ปรับหน้า print ให้พอดี A4 มากขึ้น (`@page margin: 10mm 12mm`)
- ปรับข้อความให้ดูทางการมากขึ้น
  - ตัด emoji ในหัวข้อช่วงเวลา
  - ตัด emoji ในสถานะ VM/สถานะการปกป้อง
- แก้โครงสร้าง render cell ในตาราง Summary ให้มี key ที่ชัดเจน
  (ลดความเสี่ยง warning จาก fragment key)
- ปรับ badge branding จาก `WUH` เป็น `VMR` สำหรับเอกสารรายงาน

### 5) Code Cleanup
- ลบ comment ที่ซ้ำ
- ปรับ dependency ของ `useMemo` ให้ครอบคลุม `showReport` และ `actualTimeRange`
  เพื่อให้ข้อมูลกราฟอัปเดตถูกต้องเมื่อเปิดรายงาน

## Testing Performed

### Frontend Build
- Command: `cd /opt/code/sangfor_scp/webapp/frontend && npm run build`
- Result: PASS
- Notes:
  - Build สำเร็จ
  - มี warning เดิมเรื่อง chunk size และ dynamic import (ไม่เกี่ยวกับงานนี้)

### start.sh Syntax Check
- Command: `cd /opt/code/sangfor_scp/webapp && bash -n start.sh`
- Result: PASS

### start.sh Runtime Test
- Command: `cd /opt/code/sangfor_scp/webapp && ./start.sh`
- Result: PASS
- Observed:
  - cleanup container/network สำเร็จ
  - build image frontend/backend สำเร็จ
  - containers `vmstat-backend` และ `vmstat-frontend` start สำเร็จ

## Functional Outcome
- ผู้ใช้สามารถกดออกรายงานได้จาก Session hero โดยไม่ต้องเข้าแท็บรายงาน
- แท็บรายงานถูกถอดออกตาม requirement
- รายงานยังใช้งานได้ครบ และพิมพ์ได้เหมาะกับหน้ากระดาษมากขึ้น
