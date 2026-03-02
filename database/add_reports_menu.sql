-- 
-- Add "Reports" menu item for VM Resource Intelligence System
-- Path: /vmreport
--

-- 1. เพิ่มเมนู "Reports"
INSERT INTO webapp.menu_items (name, display_name, path, icon, parent_id, menu_type, "order", is_visible, description) 
VALUES (
    'reports',              -- name
    'Reports',              -- display_name (ตามที่ user ขอ)
    '/vmreport',            -- path
    'Assessment',           -- icon
    NULL,                   -- parent_id (top-level menu)
    'menu',                 -- menu_type
    7,                      -- order (หลัง alarms ที่ order=6)
    true,                   -- is_visible
    'ระบบรายงานทรัพยากรเครื่องเสมือน' -- description
)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    path = EXCLUDED.path,
    icon = EXCLUDED.icon,
    "order" = EXCLUDED."order",
    description = EXCLUDED.description;

-- 2. Set permissions สำหรับ roles ต่างๆ

-- Admin (level=100) → full access
INSERT INTO webapp.role_menu_permissions (role_id, menu_item_id, can_view, can_edit, can_delete)
SELECT r.id, m.id, true, true, true
FROM webapp.roles r, webapp.menu_items m
WHERE r.name = 'admin' AND m.name = 'reports'
ON CONFLICT (role_id, menu_item_id) DO UPDATE SET
    can_view = EXCLUDED.can_view,
    can_edit = EXCLUDED.can_edit,
    can_delete = EXCLUDED.can_delete;

-- Manager (level=50) → can view and edit
INSERT INTO webapp.role_menu_permissions (role_id, menu_item_id, can_view, can_edit, can_delete)
SELECT r.id, m.id, true, true, false
FROM webapp.roles r, webapp.menu_items m
WHERE r.name = 'manager' AND m.name = 'reports'
ON CONFLICT (role_id, menu_item_id) DO UPDATE SET
    can_view = EXCLUDED.can_view,
    can_edit = EXCLUDED.can_edit,
    can_delete = EXCLUDED.can_delete;

-- Viewer (level=10) → view-only
INSERT INTO webapp.role_menu_permissions (role_id, menu_item_id, can_view, can_edit, can_delete)
SELECT r.id, m.id, true, false, false
FROM webapp.roles r, webapp.menu_items m
WHERE r.name = 'viewer' AND m.name = 'reports'
ON CONFLICT (role_id, menu_item_id) DO UPDATE SET
    can_view = EXCLUDED.can_view,
    can_edit = EXCLUDED.can_edit,
    can_delete = EXCLUDED.can_delete;

-- 3. Grant permissions สำหรับ roles อื่นๆ ที่มีอยู่ (ถ้ามี)
INSERT INTO webapp.role_menu_permissions (role_id, menu_item_id, can_view, can_edit, can_delete)
SELECT r.id, m.id,
    CASE 
        WHEN r.level >= 100 THEN true  -- super_admin
        WHEN r.level >= 50 THEN true   -- operator, manager
        WHEN r.level >= 10 THEN true   -- viewer
        ELSE false
    END AS can_view,
    CASE 
        WHEN r.level >= 100 THEN true
        WHEN r.level >= 50 THEN true
        ELSE false
    END AS can_edit,
    CASE 
        WHEN r.level >= 100 THEN true
        ELSE false
    END AS can_delete
FROM webapp.roles r, webapp.menu_items m
WHERE m.name = 'reports'
  AND r.name NOT IN ('admin', 'manager', 'viewer')  -- ข้ามที่เพิ่มแล้ว
ON CONFLICT (role_id, menu_item_id) DO UPDATE SET
    can_view = EXCLUDED.can_view,
    can_edit = EXCLUDED.can_edit,
    can_delete = EXCLUDED.can_delete;

-- 4. Verify installation
SELECT 
    'Reports menu added: ' || m.display_name || ' (' || m.path || ')' AS status,
    'Permissions: ' || COUNT(rmp.id) || ' roles' AS permissions
FROM webapp.menu_items m
LEFT JOIN webapp.role_menu_permissions rmp ON rmp.menu_item_id = m.id
WHERE m.name = 'reports'
GROUP BY m.id, m.display_name, m.path;
