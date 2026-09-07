# 📋 CHANGELOG - Odoo LXC Backup & Restore

> บันทึกการเปลี่ยนแปลงทั้งหมด

---

## [Unreleased] - วันที่

### 🐛 Fixed

- **ทั้ง 5 Scripts:**
  - เปลี่ยนจาก `set -e` เป็น `set -o pipefail` (แก้ปัญหา `((var++))` crash)
  - เพิ่มการ Initialize ตัวแปร `passed=0; failed=0`
  - ใช้ `mapfile` แทน pipe `while read` (แก้ปัญหา subshell)

- **[`backup-lxc.sh`](scripts/backup-lxc.sh):**
  - เปลี่ยน `pvesm lxc` → `pct config` (Proxmox command ที่ถูกต้อง)
  - เปลี่ยน `pct export` → `vzdump` (Proxmox command ที่ถูกต้อง)
  - เพิ่มการตรวจสอบ Disk space ก่อน backup
  - เพิ่ม Logging ไปที่ `logs/backup-*.log`
  - เพิ่ม Color output
  - เพิ่ม Timeout สำหรับ backup

- **[`restore-lxc.sh`](scripts/restore-lxc.sh):**
  - เปลี่ยน `pvesm lxc delete` → `pct destroy`
  - เพิ่ม Confirm prompt ก่อน destructive operation
  - เพิ่ม Health check หลัง restore
  - เพิ่ม `--force` flag สำหรับ automation
  - เพิ่ม `--nostart` flag สำหรับ manual start
  - เพิ่ม Logging
  - เพิ่ม Color output

- **[`verify-backup.sh`](scripts/verify-backup.sh):**
  - เพิ่มการตรวจสอบ file size (ไม่ใช่ 0 byte)
  - เพิ่ม `--checksum` flag สำหรับ SHA256 verification
  - เพิ่ม `--verbose` flag
  - เพิ่ม Logging
  - เพิ่ม Color output

- **[`list-backups.sh`](scripts/list-backups.sh):**
  - เพิ่ม `--id` flag เพื่อ filter ตาม LXC ID
  - เพิ่ม `--latest N` flag เพื่อแสดงเฉพาะ N backup ล่าสุด
  - เพิ่ม `--sort SIZE|DATE` flag
  - เพิ่ม `--json` flag สำหรับ JSON output
  - เพิ่ม `--summary` flag สำหรับ summary only
  - เพิ่ม Table output พร้อมสี
  - เพิ่มแสดงอายุ (age) ของ backup
  - เพิ่ม Logging

- **[`cleanup-old-backups.sh`](scripts/cleanup-old-backups.sh):**
  - เพิ่มการแสดงขนาดไฟล์ที่จะลบ
  - เพิ่ม `--force` flag สำหรับ automation
  - เพิ่มการแสดงอายุ (age) ของไฟล์
  - เพิ่ม Logging
  - เพิ่ม Color output

### ⚠️ Known Issues

- **macOS bash 3.2:** Scripts อาจมีปัญหากับ `local` นอก function ใน bash 3.2
- **Proxmox Commands:** `--maxfiles` และ `--remove` options ควรตรวจสอบกับ `vzdump --help` อีกครั้ง

---

## [1.0.0] - 2026-09-06

### ✨ Added

- สร้าง Scripts ทั้ง 5 ตัว:
  - [`backup-lxc.sh`](scripts/backup-lxc.sh) - Backup LXC Container
  - [`restore-lxc.sh`](scripts/restore-lxc.sh) - Restore LXC Container
  - [`list-backups.sh`](scripts/list-backups.sh) - แสดงรายการ Backup
  - [`verify-backup.sh`](scripts/verify-backup.sh) - ตรวจสอบความสมบูรณ์ Backup
  - [`cleanup-old-backups.sh`](scripts/cleanup-old-backups.sh) - ลบ Backup เก่า
- สร้าง [`config/backup.conf`](config/backup.conf) - Configuration file
- สร้าง [`README.md`](README.md) - เอกสารประกอบ
- สร้าง [`docs/usage-guide.md`](docs/usage-guide.md) - คู่มือการใช้งาน
