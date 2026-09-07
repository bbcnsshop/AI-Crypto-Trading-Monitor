#!/bin/bash
# cleanup-old-backups.sh
# ลบ backup เก่าตาม retention policy

# ❌ ห้ามใช้ set -e เพราะ ((var++)) จะทำให้ exit ผิด
set -o pipefail

# ========================================
# CONFIG
# ========================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/../config/backup.conf"
if [[ -f "$CONFIG_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$CONFIG_FILE"
fi

# Default values
BACKUP_DIR="${BACKUP_DIR:-/mnt/backups/odoo-lxc}"
LXC_NAME="${LXC_NAME:-odoo}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
RETENTION_WEEKS="${RETENTION_WEEKS:-4}"
RETENTION_MONTHS="${RETENTION_MONTHS:-6}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
LOG_DIR="${SCRIPT_DIR}/../logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/cleanup-$(date +%Y%m%d).log"

log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${message}" | tee -a "$LOG_FILE"
}

# ========================================
# FUNCTIONS
# ========================================

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Cleanup old LXC backups based on retention policy

Options:
  --dry-run        แสดงเฉพาะไฟล์ที่จะถูกลบ (ไม่ลบจริง)
  --days N         รักษาไว้กี่วัน (default: $RETENTION_DAYS)
  --weeks N        รักษาไว้กี่สัปดาห์ (default: $RETENTION_WEEKS)
  --months N       รักษาไว้กี่เดือน (default: $RETENTION_MONTHS)
  --id ID          ลบเฉพาะ backup ของ LXC ID นี้
  -h, --help       แสดงการใช้งาน

Examples:
  $0 --dry-run
  $0 --days 30
  $0 --id 100 --dry-run
EOF
    exit 0
}

# คำนวณวันตัดเขตเป็น YYYYMMDD
calculate_cutoff_date() {
    local days=$1

    # ใช้ date string แทน timestamp เพื่อเปรียบเทียบกับ filename
    if date -d "-${days} days" +%Y%m%d &>/dev/null; then
        date -d "-${days} days" +%Y%m%d
    elif gdate -d "-${days} days" +%Y%m%d &>/dev/null; then
        gdate -d "-${days} days" +%Y%m%d
    else
        # macOS fallback
        date -v -"${days}"d +%Y%m%d
    fi
}

# ดึงวันที่จากชื่อไฟล์ (YYYYMMDD)
extract_date_from_filename() {
    local filename="$1"
    # รูปแบบ: odoo_id100_20240101_120000.tar
    # หรือ: vzdump-lxc-100-2024_01_01-12_00_00.tar
    echo "$filename" | grep -oE '_[0-9]{8}_[0-9]{6}' | head -1 | sed 's/_//'
}

# ตรวจสอบว่าเป็น LXC backup
is_lxc_backup() {
    local filename="$1"
    [[ "$filename" =~ ^${LXC_NAME}_id[0-9]+_[0-9]{8}_[0-9]{6}\.tar$ ]] || \
    [[ "$filename" =~ ^vzdump-lxc-[0-9]+-[0-9]{8}_[0-9]{6}\.tar$ ]] || \
    [[ "$filename" =~ ^vzdump-lxc-[0-9]+-[0-9]{4}_[0-9]{2}_[0-9]{2}-[0-9]{2}_[0-9]{2}_[0-9]{2}\.tar$ ]]
}

# คำนวณอายุ (วัน)
calculate_age_days() {
    local filename="$1"
    local file_date_str=$(extract_date_from_filename "$filename")

    if [[ -z "$file_date_str" ]] || [[ ! "$file_date_str" =~ ^[0-9]{8}$ ]]; then
        echo "-1"
        return
    fi

    local file_timestamp
    if date -d "${file_date_str}" +%s &>/dev/null; then
        file_timestamp=$(date -d "${file_date_str}" +%s)
    elif gdate -d "${file_date_str}" +%s &>/dev/null; then
        file_timestamp=$(gdate -d "${file_date_str}" +%s)
    else
        echo "-1"
        return
    fi

    local now=$(date +%s)
    local age_seconds=$((now - file_timestamp))
    local age_days=$((age_seconds / 86400))
    echo "$age_days"
}

# ========================================
# MAIN
# ========================================

# Parse options
DRY_RUN=false
SPECIFIC_ID=""
FORCE_MODE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE_MODE=true
            shift
            ;;
        --days)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --weeks)
            RETENTION_WEEKS="$2"
            shift 2
            ;;
        --months)
            RETENTION_MONTHS="$2"
            shift 2
            ;;
        --id)
            SPECIFIC_ID="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            ;;
    esac
done

# ตรวจสอบ backup directory
if [[ ! -d "$BACKUP_DIR" ]]; then
    log "ERROR" "Backup directory not found: $BACKUP_DIR"
    echo -e "${RED}❌ Backup directory not found: ${BACKUP_DIR}${NC}"
    exit 1
fi

# คำนวณ cutoff date เป็น YYYYMMDD (เปรียบเทียบ string ได้เลย)
cutoff_date=$(calculate_cutoff_date "$RETENTION_DAYS")

log "INFO" "=== Cleanup Old Backups ==="
log "INFO" "Backup directory: ${BACKUP_DIR}"
log "INFO" "Retention: ${RETENTION_DAYS} days, ${RETENTION_WEEKS} weeks, ${RETENTION_MONTHS} months"
log "INFO" "Cutoff date: ${cutoff_date} (files older than this will be removed)"

echo -e "${GREEN}=== Cleanup Old Backups ===${NC}"
echo "Backup directory: ${BACKUP_DIR}"
echo "Retention: ${RETENTION_DAYS} days, ${RETENTION_WEEKS} weeks, ${RETENTION_MONTHS} months"
echo "Cutoff date: ${cutoff_date} (files older than this will be removed)"
[[ -n "$SPECIFIC_ID" ]] && echo "Filter: LXC ID ${SPECIFIC_ID} only"
echo ""

# หาไฟล์ทั้งหมด
mapfile -t all_files < <(find "$BACKUP_DIR" -maxdepth 1 -name "*.tar" -type f 2>/dev/null)

echo "Found ${#all_files[@]} backup files to check..."
echo ""

# Initialize counters
removed_count=0
kept_count=0
to_remove=()
to_keep=()

# วนลูปตรวจสอบแต่ละไฟล์
for file in "${all_files[@]}"; do
    [[ -z "$file" ]] && continue
    [[ ! -f "$file" ]] && continue

    local filename=$(basename "$file")

    # ตรวจสอบว่าเป็น LXC backup หรือไม่
    if ! is_lxc_backup "$filename"; then
        kept_count=$((kept_count + 1))
        continue
    fi

    # ตรวจสอบว่าเป็น ID ที่ต้องการหรือไม่ (ถ้าระบุ)
    if [[ -n "$SPECIFIC_ID" ]]; then
        if [[ ! "$filename" =~ id${SPECIFIC_ID}_ ]]; then
            kept_count=$((kept_count + 1))
            continue
        fi
    fi

    # ดึงวันที่จากชื่อไฟล์
    local file_date_str=$(extract_date_from_filename "$filename")

    if [[ -z "$file_date_str" ]] || [[ ! "$file_date_str" =~ ^[0-9]{8}$ ]]; then
        echo -e "${YELLOW}⚠️  Skipping (invalid date format): ${filename}${NC}"
        kept_count=$((kept_count + 1))
        continue
    fi

    # เปรียบเทียบ string (YYYYMMDD)
    if [[ "$file_date_str" < "$cutoff_date" ]]; then
        to_remove+=("$file")
        removed_count=$((removed_count + 1))
    else
        to_keep+=("$file")
        kept_count=$((kept_count + 1))
    fi
done

# แสดงผลลัพธ์
echo ""
echo -e "${GREEN}=== Summary ===${NC}"
echo "Files to remove: $removed_count"
echo "Files to keep: $kept_count"
echo ""

if [[ ${#to_remove[@]} -gt 0 ]]; then
    if [[ "$DRY_RUN" == true ]]; then
        echo -e "${YELLOW}⚠️  DRY RUN - These files would be removed:${NC}"
        local total_size=0
        for file in "${to_remove[@]}"; do
            local size=$(du -h "$file" 2>/dev/null | awk '{print $1}')
            local age=$(calculate_age_days "$(basename "$file")")
            echo -e "  ${RED}📄${NC} $(basename "$file") - ${size} (${age}d old)"
            total_size=$(($total_size + $(du -k "$file" 2>/dev/null | awk '{print $1}')))
        done
        echo ""
        echo "Total size to free: $(($total_size / 1024))MB"
        echo ""
        echo -e "${BLUE}💡 Run without --dry-run to actually remove these files${NC}"
    else
        if [[ "$FORCE_MODE" != "true" ]]; then
            echo -e "${YELLOW}⚠️  About to remove ${#to_remove[@]} backup files${NC}"
            read -p "Continue? (yes/no): " -r
            if [[ ! "$REPLY" =~ ^[Yy][Ee][Ss]$ ]]; then
                echo "Cancelled."
                exit 0
            fi
        fi

        echo -e "${RED}🗑️  Removing old backups...${NC}"
        local removed_size=0
        for file in "${to_remove[@]}"; do
            local size=$(du -h "$file" 2>/dev/null | awk '{print $1}')
            echo "  Removing: $(basename "$file") (${size})"
            if rm -f "$file"; then
                log "INFO" "Removed: $(basename "$file")"
                removed_size=$(($removed_size + $(du -k "$file" 2>/dev/null | awk '{print $1}')))
            else
                log "ERROR" "Failed to remove: $(basename "$file")"
                echo -e "${RED}❌ Failed to remove: $(basename "$file")${NC}"
            fi
        done
        echo ""
        echo -e "${GREEN}✅ Cleanup completed! Removed $removed_count old backups.${NC}"
        echo "Space freed: $(($removed_size / 1024))MB"
    fi
else
    echo -e "${GREEN}✅ No old backups to remove.${NC}"
fi

log "INFO" "Cleanup done: ${removed_count} removed, ${kept_count} kept"
exit 0
