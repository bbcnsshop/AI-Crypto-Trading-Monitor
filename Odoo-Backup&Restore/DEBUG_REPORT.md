# 🪲 Debug Report - Odoo LXC Backup & Restore

> 📅 วันที่: 2026-09-07
> 👤 Debug by: BB (Bot Boss)
> 🎯 Scope: scripts/*.sh ทั้ง 5 ตัว

---

## ⚠️ หมายเหตุสำคัญ

**BB ไม่ได้รัน script จริงบน Proxmox VE** เพราะ:
- ไม่มี Proxmox VE environment
- ไม่ได้รับอนุญาตให้ live-test
- ใช้แค่ `bash -n` syntax check + manual review เท่านั้น

**สิ่งที่ BB ยืนยันได้:**
- ✅ Syntax ผ่าน `bash -n`
- ❌ มีปัญหา `local` นอก function ใน bash 3.2 (macOS default)

---

## 🐛 ปัญหาที่พบจริง (Verified)

### 1. ❌ Bug จริง: `local` นอก function

**ทดสอบ:** `bash -c 'local x=1'` ใน bash 3.2.57 (macOS) → error
```
bash: line 0: local: can only be used in a function
```

**ไฟล์ที่มีปัญหา:**

#### [`scripts/list-backups.sh`](scripts/list-backups.sh)
| Line | Code | ปัญหา |
|------|------|-------|
| 221 | `local filename=$(basename "$file")` | local นอก function |
| 224 | `local lxc_id=$(extract_lxc_id "$filename")` | local นอก function |
| 280 | `local filename=$(basename "$file")` | local นอก function |
| 281 | `local lxc_id=$(extract_lxc_id "$filename")` | local นอก function |
| 282 | `local size=$(du -h ...)` | local นอก function |
| 283 | `local date_str=$(extract_date ...)` | local นอก function |
| 284 | `local age=$(calculate_age_days ...)` | local นอก function |
| 288 | `local formatted_date=...` | local นอก function |
| 290 | `local formatted_date=...` | local นอก function |
| 294 | `local age_color=...` | local นอก function |

#### [`scripts/cleanup-old-backups.sh`](scripts/cleanup-old-backups.sh)
| Line | Code | ปัญหา |
|------|------|-------|
| 211 | `local filename=$(basename "$file")` | local นอก function |
| 228 | `local file_date_str=$(extract_date_from_filename ...)` | local นอก function |
| 256 | `local total_size=0` | local นอก function |
| 258 | `local size=$(du -h ...)` | local นอก function |
| 259 | `local age=$(calculate_age_days ...)` | local นอก function |
| 278 | `local removed_size=0` | local นอก function |
| 280 | `local size=$(du -h ...)` | local นอก function |

**ผลกระทบ:** Script จะ error ทันทีเมื่อรันบน bash 3.2 (macOS default) หรือ bash ที่ strict mode เปิด

**ทางแก้:** เอา `local` ออก หรือห่อ code ใน function

---

### 2. ⚠️ Bug ที่ BB สงสัย (ยังไม่ได้ทดสอบ)

#### Pattern matching หลวมใน `restore-lxc.sh:80`
```bash
find "${BACKUP_DIR}" -maxdepth 1 -name "*${LXC_NAME}*id${lxc_id}*_*.tar*" -type f
```
- Pattern `*${LXC_NAME}*id${lxc_id}*` จะ match `id10` กับ `id1001` ด้วย
- ควรใช้ regex ที่เข้มงวด: `^${LXC_NAME}_id${lxc_id}_[0-9]{8}_[0-9]{6}\.tar$`

#### vzdump options ใน `backup-lxc.sh:142-143`
```bash
--maxfiles 1
--remove 0
```
- BB ไม่แน่ใจ 100% ว่า option ทั้งสองทำงานร่วมกันยังไง
- `--maxfiles 1` = เก็บแค่ 1 file ต่อ container
- `--remove 0` = ไม่ลบ backup เก่า
- → Conflict กับ `cleanup_old_backups()` ที่ลบเอง

#### `awk '{print $2}'` ในการ parse `pct status`
```bash
pct status "$lxc_id" 2>/dev/null | awk '{print $2}'
```
- Output: `status: running` → ได้ `running` ✓
- แต่ถ้า LXC มี status อื่น เช่น `stopped`, `paused` → ทำงานถูก
- ถ้า output format เปลี่ยนใน Proxmox เวอร์ชันใหม่ → อาจพัง

---

### 3. ✅ ที่ BB คิดว่า OK แต่ไม่ได้ทดสอบ

- `set -o pipefail` แทน `set -e` → ถูกต้อง
- Initialize `passed=0; failed=0` → ถูกต้อง
- ใช้ `mapfile` แทน pipe `while read` → ถูกต้อง
- Date comparison เป็น YYYYMMDD string → ถูกต้อง
- ใช้ `grep -oE` แทน `grep -oP` → portable กว่า

---

## 🔧 สิ่งที่ต้องทำต่อ

| # | งาน | สถานะ |
|---|------|--------|
| 1 | เอา `local` ออกจาก main script (list-backups, cleanup-old-backups) | ❌ ยังไม่ทำ |
| 2 | ทดสอบ script บน Proxmox VE จริง | ❌ ไม่ได้ทำ |
| 3 | เช็ค vzdump options กับ Proxmox docs | ❌ ไม่ได้ทำ |
| 4 | เช็ค pct restore syntax | ❌ ไม่ได้ทำ |
| 5 | เช็ค pct destroy options | ❌ ไม่ได้ทำ |

---

## 📊 สรุป

| Category | จำนวน |
|----------|--------|
| ❌ Bug ที่ยืนยันได้ (verified) | 1 (local นอก function) |
| ⚠️ Bug ที่สงสัย (ไม่ได้ทดสอบ) | 3 |
| ✅ น่าจะ OK (ไม่ได้ทดสอบ) | 5+ |

**คำแนะนำ:**
- ⚠️ **อย่าใช้ script เหล่านี้บน Proxmox production จนกว่าจะ:**
  1. แก้ปัญหา `local` นอก function
  2. ทดสอบบน Proxmox VE จริง
  3. ตรวจสอบ Proxmox commands กับ docs

---

## 🔍 Proxmox VE Commands Verification (BB's Knowledge)

> ⚠️ BB ไม่สามารถเข้าถึง internet ได้โดยตรง - ใช้ความรู้จาก training data (cutoff Jan 2026)
> ⚠️ ควรตรวจสอบกับ `command --help` บน Proxmox จริงอีกครั้ง

### ✅ Commands ที่ถูกต้องแน่นอน

| Command | ใช้ในไฟล์ | สถานะ |
|---------|-----------|--------|
| `pct config <vmid>` | [`backup-lxc.sh:85`](scripts/backup-lxc.sh:85) | ✅ ถูก |
| `pct status <vmid>` | [`backup-lxc.sh:122`](scripts/backup-lxc.sh:122), [`restore-lxc.sh:106,128,172`](scripts/restore-lxc.sh:106) | ✅ ถูก |
| `pct stop <vmid>` | [`restore-lxc.sh:134`](scripts/restore-lxc.sh:134) | ✅ ถูก |
| `pct destroy <vmid>` | [`restore-lxc.sh:140`](scripts/restore-lxc.sh:140) | ✅ ถูก (ต้อง stop ก่อน) |
| `pct start <vmid>` | [`restore-lxc.sh:166`](scripts/restore-lxc.sh:166) | ✅ ถูก |
| `pct list` | [`backup-lxc.sh:262`](scripts/backup-lxc.sh:262) | ✅ ถูก |

### ⚠️ Commands ที่น่าจะถูก แต่ต้องเช็ค

| Command | ใช้ในไฟล์ | สถานะ | ต้องเช็ค |
|---------|-----------|--------|----------|
| `pct restore <vmid> <archive> --storage local` | [`restore-lxc.sh:152`](scripts/restore-lxc.sh:152) | ⚠️ น่าจะถูก | format ของ archive ที่รับ |
| `vzdump --dumpdir --storage --compress --mode` | [`backup-lxc.sh:136-144`](scripts/backup-lxc.sh:136) | ⚠️ น่าจะถูก | option ทั้งหมด |

### ❌ Options ที่ BB ไม่แน่ใจ

#### `vzdump --maxfiles 1` และ `--remove 0`
```bash
--maxfiles 1    # BB ไม่แน่ใจ 100% ว่ามี option นี้
--remove 0      # BB ไม่แน่ใจ 100% ว่ามี option นี้
```
- `--maxfiles`: อาจหมายถึงเก็บ backup แค่ N ไฟล์ต่อ VM
- `--remove`: อาจหมายถึง retention mode (0 = ไม่ลบ, 1 = ลบ)
- **คำแนะนำ:** รัน `vzdump --help` บน Proxmox จริงเพื่อยืนยัน

#### `pct restore` format ที่รับ
- ปกติ `pct restore` คาดหวัง vzdump format (`.tar.zst`, `.tar.gz`)
- ถ้า backup file เป็น `.tar` เฉยๆ อาจไม่รับ
- **คำแนะนำ:** ใช้ `pct restore --help` เช็ค

---

## 📊 สรุปการตรวจสอบ Proxmox Commands

| หมวด | จำนวน |
|------|--------|
| ✅ ถูกแน่นอน | 6 commands |
| ⚠️ น่าจะถูก ต้องเช็คเพิ่ม | 2 commands |
| ❌ ไม่แน่ใจ 100% | 2 options |

**คำแนะนำสำคัญ:**
1. รัน `vzdump --help` บน Proxmox จริงเพื่อยืนยัน `--maxfiles` และ `--remove`
2. รัน `pct restore --help` เพื่อเช็ค format ที่รับ
3. ทดสอบ backup/restore บน LXC ที่ไม่ใช่ production ก่อน

---

## � ติดต่อ

พบปัญหาเพิ่มเติม → บอก BB ได้เลยครับ
