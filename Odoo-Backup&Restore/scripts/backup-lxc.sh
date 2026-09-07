#!/bin/bash
# backup-lxc.sh
# สำหรับ Backup LXC Container ด้วย vzdump
# เลือก LXC ID ได้หลายตัว

# ❌ ห้ามใช้ set -e เพราะ ((var++)) และ pipe จะทำให้ exit ผิด
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
LXC_ID="${LXC_ID:-}"
BACKUP_DIR="${BACKUP_DIR:-/mnt/backups/odoo-lxc}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
RETENTION_WEEKS="${RETENTION_WEEKS:-4}"
RETENTION_MONTHS="${RETENTION_MONTHS:-6}"
LXC_NAME="${LXC_NAME:-odoo}"
COMPRESSION_LEVEL="${COMPRESSION_LEVEL:-6}"
BACKUP_MODE="${BACKUP_MODE:-snapshot}"
BACKUP_TIMEOUT="${BACKUP_TIMEOUT:-3600}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging
LOG_DIR="${SCRIPT_DIR}/../logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/backup-$(date +%Y%m%d).log"

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
Usage: $0 [OPTIONS] [LXC_ID ...]

Backup LXC Container(s) using vzdump

Arguments:
  LXC_ID       LXC ID ที่ต้องการ backup (พิมพ์ได้หลายตัว)
               เช่น: $0 100 101 102
               หรือ: $0 --all

Options:
  --all        backup ทุก LXC container
  --dir DIR    ตำแหน่งเก็บ backup (default: $BACKUP_DIR)
  --mode MODE  snapshot, suspend, stop (default: $BACKUP_MODE)
  --compress N compression level 1-9 (default: $COMPRESSION_LEVEL)
  -h, --help   แสดงการใช้งาน
EOF
    exit 0
}

# ตรวจสอบว่าเป็นตัวเลข
is_number() {
    [[ "$1" =~ ^[0-9]+$ ]]
}

# ตรวจสอบว่า LXC มีอยู่จริง
lxc_exists() {
    local lxc_id="$1"
    if ! is_number "$lxc_id"; then
        return 1
    fi
    # ใช้ pct config แทน pvesm list
    pct config "$lxc_id" &>/dev/null
}

# ตรวจสอบ disk space
check_disk_space() {
    local target_dir="$1"
    if [[ ! -d "$target_dir" ]]; then
        log "ERROR" "Backup directory not found: $target_dir"
        return 1
    fi
    local available=$(df -BG "$target_dir" | awk 'NR==2 {print $4}' | tr -d 'G')
    if [[ "$available" -lt 5 ]]; then
        log "WARN" "Low disk space: ${available}GB available"
        echo -e "${YELLOW}⚠️  Low disk space: ${available}GB${NC}"
    fi
}

# Backup Container แบบเดียว
backup_container() {
    local lxc_id="$1"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_name="vzdump-lxc-${lxc_id}-${timestamp}"
    local tar_path="${BACKUP_DIR}/${LXC_NAME}_id${lxc_id}_${timestamp}.tar"

    log "INFO" "=== Backup LXC Container ID: ${lxc_id} ==="
    echo -e "${GREEN}=== Backup LXC Container ID: ${lxc_id} ===${NC}"
    echo "Backup name: ${backup_name}"
    echo "Target: ${tar_path}"

    # ตรวจสอบ LXC
    if ! lxc_exists "$lxc_id"; then
        log "ERROR" "LXC Container ID ${lxc_id} not found!"
        echo -e "${RED}❌ Error: LXC Container ID ${lxc_id} not found!${NC}"
        return 1
    fi

    # ตรวจสอบสถานะ LXC
    local status=$(pct status "$lxc_id" 2>/dev/null | awk '{print $2}')
    log "INFO" "LXC ${lxc_id} status: ${status}"
    echo "LXC status: ${status}"

    # ตรวจสอบ disk space
    check_disk_space "$BACKUP_DIR"

    # สร้าง backup directory ถ้ายังไม่มี
    mkdir -p "$BACKUP_DIR"

    # ใช้ vzdump แทน pct export
    log "INFO" "Running vzdump for LXC ${lxc_id}..."
    echo "Creating backup with vzdump..."

    local vzdump_opts=(
        "$lxc_id"
        --dumpdir "$BACKUP_DIR"
        --storage "local"
        --compress "zstd"
        --mode "$BACKUP_MODE"
        --maxfiles 1
        --remove 0
    )

    if timeout "$BACKUP_TIMEOUT" vzdump "${vzdump_opts[@]}" >> "$LOG_FILE" 2>&1; then
        log "INFO" "vzdump completed for LXC ${lxc_id}"
        echo -e "${GREEN}✅ Backup completed: ${lxc_id}${NC}"
        return 0
    else
        local rc=$?
        log "ERROR" "vzdump failed for LXC ${lxc_id} (rc=${rc})"
        echo -e "${RED}❌ Error: Backup failed for LXC ${lxc_id} (rc=${rc})${NC}"
        return 1
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    log "INFO" "=== Cleanup old backups ==="
    echo -e "${GREEN}=== Cleanup old backups ===${NC}"

    # คำนวณ cutoff date เป็น YYYYMMDD
    local cutoff_date
    if date -d "-${RETENTION_DAYS} days" +%Y%m%d &>/dev/null; then
        cutoff_date=$(date -d "-${RETENTION_DAYS} days" +%Y%m%d)
    else
        cutoff_date=$(gdate -d "-${RETENTION_DAYS} days" +%Y%m%d 2>/dev/null || date -v -"${RETENTION_DAYS}"d +%Y%m%d)
    fi

    echo "Cutoff date: ${cutoff_date} (removing files older than this)"

    # หาไฟล์ที่ตรง pattern
    local removed=0
    local kept=0

    while IFS= read -r file; do
        [[ -z "$file" ]] && continue
        local filename=$(basename "$file")
        # ดึง YYYYMMDD จาก filename (8 หลักแรกหลัง _idXXX_)
        local date_part=$(echo "$filename" | grep -oE '_[0-9]{8}_[0-9]{6}\.tar$' | grep -oE '[0-9]{8}')

        if [[ -z "$date_part" ]]; then
            kept=$((kept + 1))
            continue
        fi

        if [[ "$date_part" < "$cutoff_date" ]]; then
            log "INFO" "Removing old backup: ${file}"
            echo "Removing: ${filename}"
            rm -f "$file"
            removed=$((removed + 1))
        else
            kept=$((kept + 1))
        fi
    done < <(find "${BACKUP_DIR}" -maxdepth 1 -name "${LXC_NAME}_id*_*.tar" -type f 2>/dev/null)

    log "INFO" "Cleanup done: ${removed} removed, ${kept} kept"
    echo "Cleanup: ${removed} removed, ${kept} kept"
}

# ========================================
# MAIN
# ========================================

# Parse options
TARGET_IDS=()
BACKUP_ALL=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage
            ;;
        --all)
            BACKUP_ALL=true
            shift
            ;;
        --dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --mode)
            BACKUP_MODE="$2"
            shift 2
            ;;
        --compress)
            COMPRESSION_LEVEL="$2"
            shift 2
            ;;
        [0-9]*)
            TARGET_IDS+=("$1")
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            ;;
    esac
done

# ตรวจสอบ prerequisites
if ! command -v vzdump &>/dev/null; then
    log "ERROR" "vzdump not found. This script must run on Proxmox VE host."
    echo -e "${RED}❌ Error: vzdump not found. Run on Proxmox VE host.${NC}"
    exit 1
fi

if [[ ! -d "$BACKUP_DIR" ]]; then
    log "WARN" "Creating backup directory: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
fi

# Main logic
if [[ "$BACKUP_ALL" == true ]]; then
    log "INFO" "=== Backup All LXC Containers ==="
    echo -e "${GREEN}=== Backup All LXC Containers ===${NC}"

    # ดึง LXC IDs ทั้งหมด
    while IFS= read -r id; do
        [[ -n "$id" ]] && TARGET_IDS+=("$id")
    done < <(pct list 2>/dev/null | awk 'NR>1 {print $1}')

elif [[ ${#TARGET_IDS[@]} -eq 0 ]] && [[ -n "$LXC_ID" ]]; then
    # ใช้ LXC_ID จาก config
    for id in $LXC_ID; do
        TARGET_IDS+=("$id")
    done
fi

if [[ ${#TARGET_IDS[@]} -eq 0 ]]; then
    echo -e "${YELLOW}❌ No LXC ID specified${NC}"
    usage
fi

# Backup แต่ละ container
SUCCESS=0
FAILED=0

for id in "${TARGET_IDS[@]}"; do
    if is_number "$id"; then
        if backup_container "$id"; then
            SUCCESS=$((SUCCESS + 1))
        else
            FAILED=$((FAILED + 1))
        fi
    else
        log "WARN" "Invalid LXC ID: ${id}"
        echo -e "${YELLOW}⚠️ Warning: '${id}' is not a valid number, skipping...${NC}"
        FAILED=$((FAILED + 1))
    fi
done

# Cleanup
cleanup_old_backups

# Summary
log "INFO" "=== Summary: ${SUCCESS} success, ${FAILED} failed ==="
echo ""
echo -e "${GREEN}=== Summary ===${NC}"
echo "Success: ${SUCCESS}"
echo "Failed:  ${FAILED}"
echo "Log:     ${LOG_FILE}"

exit $((FAILED > 0 ? 1 : 0))
