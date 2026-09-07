# 📖 Quick Reference - Odoo LXC Backup & Restore

> คู่มือการใช้งานฉบับย่อ

---

## 🚀 Quick Start

### ติดตั้ง
```bash
# Clone หรือ Copy โฟลเดอร์นี้ไปที่ Proxmox VE host
# ทำให้ script รันได้
chmod +x scripts/*.sh
```

### Backup LXC
```bash
# Backup LXC ID 100
./scripts/backup-lxc.sh 100

# Backup หลาย ID
./scripts/backup-lxc.sh 100 101 102

# Backup ทุก container
./scripts/backup-lxc.sh --all
```

### Restore LXC
```bash
# Restore จาก backup ล่าสุด (ต้องยืนยัน)
./scripts/restore-lxc.sh 100

# Restore จากไฟล์ที่ระบุ
./scripts/restore-lxc.sh --file /path/to/backup.tar 100

# Restore โดยไม่ถาม (automation)
./scripts/restore-lxc.sh --force --latest 100

# Restore แล้วไม่ start
./scripts/restore-lxc.sh --nostart 100
```

### ดูรายการ Backup
```bash
# ดูทั้งหมด
./scripts/list-backups.sh

# ดูเฉพาะ LXC ID 100
./scripts/list-backups.sh --id 100

# ดู 5 backup ล่าสุด
./scripts/list-backups.sh --latest 5

# เรียงตามขนาด
./scripts/list-backups.sh --sort SIZE

# JSON output
./scripts/list-backups.sh --json
```

### ตรวจสอบ Backup
```bash
# ตรวจสอบทั้งหมด
./scripts/verify-backup.sh --all

# ตรวจสอบเฉพาะ LXC ID 100
./scripts/verify-backup.sh --id 100

# ตรวจสอบไฟล์ที่ระบุ
./scripts/verify-backup.sh --file /path/to/backup.tar

# ตรวจสอบแบบละเอียด
./scripts/verify-backup.sh --all --verbose

# ตรวจสอบพร้อม checksum
./scripts/verify-backup.sh --all --checksum
```

### ลบ Backup เก่า
```bash
# ดูว่าจะลบอะไร (dry run)
./scripts/cleanup-old-backups.sh --dry-run

# ลบ backup เก่ากว่า 7 วัน (default)
./scripts/cleanup-old-backups.sh

# ลบ backup เก่ากว่า 30 วัน
./scripts/cleanup-old-backups.sh --days 30

# ลบ backup เฉพาะ LXC ID 100
./scripts/cleanup-old-backups.sh --id 100

# ลบโดยไม่ถาม (automation)
./scripts/cleanup-old-backups.sh --force
```

---

## ⚙️ Configuration

แก้ไขไฟล์ `config/backup.conf`:

```bash
# LXC ID ที่ต้องการ backup
LXC_ID="100 101"

# ที่เก็บ backup
BACKUP_DIR="/mnt/backups/odoo-lxc"

# Retention policy
RETENTION_DAYS=7
RETENTION_WEEKS=4
RETENTION_MONTHS=6

# Backup mode: snapshot, suspend, stop
BACKUP_MODE="snapshot"
```

---

## 📊 Common Use Cases

### ตั้ง Cron Schedule
```bash
# Backup ทุกวันเวลา 2:00 น.
0 2 * * * /path/to/scripts/backup-lxc.sh --all >> /var/log/backup.log 2>&1

# Cleanup ทุกวันเวลา 3:00 น.
0 3 * * * /path/to/scripts/cleanup-old-backups.sh >> /var/log/cleanup.log 2>&1

# Verify ทุกสัปดาห์วันอาทิตย์
0 4 * * 0 /path/to/scripts/verify-backup.sh --all >> /var/log/verify.log 2>&1
```

### Remote Backup
```bash
# แก้ไข config/backup.conf
REMOTE_BACKUP="yes"
REMOTE_HOST="192.168.1.100"
REMOTE_DIR="/backups/odoo"
REMOTE_USER="root"
```

### Disaster Recovery
```bash
# 1. ตรวจสอบ backup
./scripts/verify-backup.sh --all

# 2. ดูรายการ backup
./scripts/list-backups.sh --id 100

# 3. Restore
./scripts/restore-lxc.sh --force --file /path/to/latest-backup.tar 100
```

---

## 🔧 Troubleshooting

### Error: "vzdump not found"
```bash
# Script ต้องรันบน Proxmox VE host
# ตรวจสอบว่ารันบน Proxmox
pveversion
```

### Error: "No space left on device"
```bash
# ตรวจสอบพื้นที่
df -h

# เพิ่ม retention days
./scripts/cleanup-old-backups.sh --days 3
```

### Error: "Permission denied"
```bash
# ตรวจสอบสิทธิ์
ls -la /mnt/backups/
chmod 755 scripts/*.sh
```

### Error: "LXC not found"
```bash
# ดู LXC ทั้งหมด
pct list

# ตรวจสอบ LXC ID ที่ถูกต้อง
```

---

## 📝 Log Files

Logs จะถูกบันทึกที่ `logs/`:
- `logs/backup-YYYYMMDD.log`
- `logs/restore-YYYYMMDD.log`
- `logs/verify-YYYYMMDD.log`
- `logs/cleanup-YYYYMMDD.log`
