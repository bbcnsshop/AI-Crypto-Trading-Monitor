# 📖 Usage Guide - Odoo LXC Backup & Restore

## 🔧 ความต้องการ

- Proxmox VE (ทดสอบบน Debian)
- `pve` และ `pvesm` command-line tools
- Bash 4+
- SSH access (สำหรับ remote backup)
- Sufficient disk space for backups

## 📋 Scripts รายการ

### 1. `backup-lxc.sh` - Backup LXC Container

**Usage:**
```bash
# Backup LXC ID 100
./scripts/backup-lxc.sh 100

# Backup multiple LXC IDs
./scripts/backup-lxc.sh 100 101 102

# Backup all LXC containers
./scripts/backup-lxc.sh --all

# Backup with specific name
./scripts/backup-lxc.sh 100 --name my-odoo

# Backup to specific directory
./scripts/backup-lxc.sh 100 --dir /mnt/backups/custom

# Dry run (show what would be backed up)
./scripts/backup-lxc.sh 100 --dry-run

# Show help
./scripts/backup-lxc.sh --help
```

**Output:**
```
=== Backup LXC Container ID: 100 ===
Backup name: odoo_id100_20240101_120000
Target: /mnt/backups/odoo-lxc/odoo_id100_20240101_120000.tar
Creating LXC snapshot...
Exporting to tarball...
✅ Backup completed: /mnt/backups/odoo-lxc/odoo_id100_20240101_120000.tar
```

### 2. `restore-lxc.sh` - Restore LXC Container

**Usage:**
```bash
# Restore LXC ID 100 from latest backup
./scripts/restore-lxc.sh 100

# Restore from specific backup file
./scripts/restore-lxc.sh --file /mnt/backups/odoo-lxc/odoo_id100_20240101_120000.tar

# Restore latest backup (use with --id)
./scripts/restore-lxc.sh --latest --id 100

# Restore and stop LXC first
./scripts/restore-lxc.sh 100 --stop

# Show help
./scripts/restore-lxc.sh --help
```

**Output:**
```
=== Restore LXC Container ID: 100 ===
Backup file: /mnt/backups/odoo-lxc/odoo_id100_20240101_120000.tar
Stopping LXC 100...
Removing old container...
Restoring from backup...
Starting LXC 100...
✅ Restore completed successfully!
```

### 3. `list-backups.sh` - Show Backup List

**Usage:**
```bash
# Show all backups
./scripts/list-backups.sh

# Show backups for specific LXC ID
./scripts/list-backups.sh --id 100

# Verbose output
./scripts/list-backups.sh --verbose

# Show help
./scripts/list-backups.sh --help
```

**Output:**
```
=== Backup List ===
Directory: /mnt/backups/odoo-lxc

📦 odoo_id100_20240101_120000.tar
   Size: 2.4G
   Date: Jan 1 12:00:00 2024

📦 odoo_id100_20231231_120000.tar
   Size: 2.3G
   Date: Dec 31 12:00:00 2023

Total backups: 2
```

### 4. `verify-backup.sh` - Verify Backup Integrity

**Usage:**
```bash
# Verify all backups
./scripts/verify-backup.sh --all

# Verify specific file
./scripts/verify-backup.sh --file /mnt/backups/odoo-lxc/odoo_id100_20240101_120000.tar

# Verify specific LXC ID backups
./scripts/verify-backup.sh --id 100

# Verbose mode
./scripts/verify-backup.sh --all --verbose

# Fix mode (if possible)
./scripts/verify-backup.sh --all --fix

# Show help
./scripts/verify-backup.sh --help
```

**Output:**
```
=== Verifying All Backups ===
✅ OK: odoo_id100_20240101_120000.tar
✅ OK: odoo_id101_20240101_120000.tar
❌ ERROR: odoo_id102_20240101_120000.tar - Invalid or corrupted tar file

Result: 2 passed, 1 failed
```

### 5. `cleanup-old-backups.sh` - Remove Old Backups

**Usage:**
```bash
# Remove backups older than 7 days
./scripts/cleanup-old-backups.sh

# Dry run (show what would be removed)
./scripts/cleanup-old-backups.sh --dry-run

# Keep backups older than 30 days
./scripts/cleanup-old-backups.sh --days 30

# Keep backups older than 12 weeks
./scripts/cleanup-old-backups.sh --weeks 12

# Remove only specific LXC ID backups
./scripts/cleanup-old-backups.sh --id 100

# Remove backups older than 6 months
./scripts/cleanup-old-backups.sh --months 6

# Show help
./scripts/cleanup-old-backups.sh --help
```

**Output:**
```
=== Cleanup Old Backups ===
Backup directory: /mnt/backups/odoo-lxc
Retention: 7 days, 4 weeks, 6 months
Cutoff date: 20231225 (files older than this will be removed)

Found 10 backup files to check...

Removing old backup: odoo_id100_20231220_120000.tar
Removing old backup: odoo_id100_20231215_120000.tar
✅ Cleanup completed! Removed 2 old backups.
```

## ⚙️ Configuration

Edit `config/backup.conf` to customize settings:

```bash
# LXC ID
LXC_ID="100"

# Backup directory
BACKUP_DIR="/mnt/backups/odoo-lxc"

# Retention
RETENTION_DAYS=7
RETENTION_WEEKS=4
RETENTION_MONTHS=6

# Remote backup (optional)
REMOTE_BACKUP="yes"
REMOTE_HOST="192.168.1.100"
```

## 📊 Scheduling with Cron

Add to crontab for automated backups:

```bash
# Backup every day at 2:00 AM
0 2 * * * /path/to/backup-lxc.sh 100 >> /var/log/backup.log 2>&1

# Cleanup old backups every Sunday at 3:00 AM
0 3 * * 0 /path/to/cleanup-old-backups.sh >> /var/log/backup.log 2>&1

# Verify backups every Saturday at 4:00 AM
0 4 * * 6 /path/to/verify-backup.sh --all >> /var/log/backup.log 2>&1
```

## 🔒 Security Notes

- Run scripts as **root** (required for pct commands)
- Store backups on **separate storage** or remote host
- Encrypt backups if containing sensitive data
- Regularly test restores to ensure backups work

## 🚨 Troubleshooting

### Backup fails
- Check LXC ID exists: `pvesm list local | grep <LXC_ID>`
- Check disk space: `df -h /mnt/backups/odoo-lxc`
- Check permissions: `ls -la /mnt/backups/odoo-lxc`

### Restore fails
- Verify backup integrity: `./scripts/verify-backup.sh --file <backup_file>`
- Check if LXC already exists: `pvem lxc <LXC_ID>`
- Ensure enough disk space for restore

### Remote backup fails
- Check SSH connectivity: `ssh root@<REMOTE_HOST>`
- Check remote directory permissions
- Verify remote storage has sufficient space