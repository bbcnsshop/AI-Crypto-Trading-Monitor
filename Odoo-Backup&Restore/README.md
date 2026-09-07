# 🔄 Odoo LXC Backup & Restore Scripts

**โฟลเดอร์สำหรับเก็บ Scripts สำหรับ Backup และ Restore LXC Container บน Proxmox Debian**

---

## 🎯 เป้าหมาย

สร้าง script บน Proxmox (Debian) เพื่อ:
1. **Backup** LXC container แบบ full snapshot
2. **Restore** LXC container ให้ข้อมูลทุกอย่างกลับมาเหมือนเดิมตอน backup
3. **Schedule** backup อัตโนมัติ (daily/weekly)

---

## ✅ สถานะ: Scripts สร้างแล้ว!

| # | Script | ไฟล์ | สถานะ |
|---|--------|------|--------|
| 1 | Backup | `scripts/backup-lxc.sh` | ✅ สร้างแล้ว |
| 2 | Restore | `scripts/restore-lxc.sh` | ✅ สร้างแล้ว |
| 3 | List | `scripts/list-backups.sh` | ✅ สร้างแล้ว |
| 4 | Verify | `scripts/verify-backup.sh` | ✅ สร้างแล้ว |
| 5 | Cleanup | `scripts/cleanup-old-backups.sh` | ✅ สร้างแล้ว |

---

## 📁 โครงสร้างโฟลเดอร์

```
odoo-backup&restore/
├── README.md                    # คำอธิบายนี้
├── scripts/
│   ├── backup-lxc.sh           # Backup LXC (เลือก ID ได้หลายตัว)
│   ├── restore-lxc.sh          # Restore LXC
│   ├── list-backups.sh         # แสดงรายการ backup
│   ├── verify-backup.sh        # ตรวจสอบความสมบูรณ์
│   └── cleanup-old-backups.sh  # ลบ backup เก่า
├── config/
│   └── backup.conf             # ตั้งค่า config
├── logs/
│   └── .gitkeep                # เก็บ logs
└── docs/
    └── usage-guide.md          # คู่มือการใช้งาน
```

---

## 🚀 Quick Start

### 1. Backup LXC
```bash
# Backup LXC ID 100
./scripts/backup-lxc.sh 100

# Backup หลาย ID
./scripts/backup-lxc.sh 100 101 102

# Backup ทุก container
./scripts/backup-lxc.sh --all
```

### 2. Restore LXC
```bash
# Restore LXC ID 100 (จาก backup ล่าสุด)
./scripts/restore-lxc.sh 100

# Restore จากไฟล์ที่ระบุ
./scripts/restore-lxc.sh --file /path/to/backup.tar
```

### 3. แสดงรายการ Backup
```bash
./scripts/list-backups.sh
```

### 4. ตรวจสอบ Backup
```bash
./scripts/verify-backup.sh --all
```

### 5. ลบ Backup เก่า
```bash
# ลบ backup เก่ากว่า 7 วัน
./scripts/cleanup-old-backups.sh

# ดูว่าจะลบอะไร (dry run)
./scripts/cleanup-old-backups.sh --dry-run
```

---

## 🔧 ตั้งค่า Config

แก้ไขไฟล์ `config/backup.conf`:

```bash
# LXC ID (ว่างไว้ = พิมพ์เองตอนรัน)
LXC_ID=""

# ชื่อ LXC
LXC_NAME="odoo"

# ที่เก็บ backup
BACKUP_DIR="/mnt/backups/odoo-lxc"

# Retention
RETENTION_DAYS=7
RETENTION_WEEKS=4
RETENTION_MONTHS=6

# Remote backup
REMOTE_BACKUP="no"
REMOTE_HOST="192.168.1.100"
```

---

## 📋 สิ่งที่ Backup ครอบคลุม

```
✅ LXC Container (full snapshot)
✅ Config files (/etc/pve/lxc/*.conf)
✅ Storage (ข้อมูล Odoo/database)
✅ Bind mounts (ถ้ามี)
✅ Custom scripts
✅ Odoo filestore (attachments, etc.)
✅ PostgreSQL database
```

---

## ⚠️ ยังต้องทำ

- [ ] ทดสอบบน Proxmox จริง
- [ ] ปรับแต่งตาม environment จริง
- [ ] ตั้งค่า crontab สำหรับ schedule อัตโนมัติ
- [ ] ทดสอบ restore จริง

---

**อัปเดต:** 6 กันยายน 2569
