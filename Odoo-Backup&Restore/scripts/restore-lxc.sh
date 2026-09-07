#!/bin/bash
# restore-lxc.sh
# สำหรับ Restore LXC Container จาก backup

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
LXC_ID="${LXC_ID:-}"
BACKUP_DIR="${BACKUP_DIR:-/mnt/backups/odoo-lxc}"
LXC_NAME="${LXC_NAME:-odoo}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
LOG_DIR="${SCRIPT_DIR}/../logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/restore-$(date +%Y%m%d).log"

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
Usage: $0 [OPTIONS] [LXC_ID]

Restore LXC Container from backup

Arguments:
  LXC_ID       LXC ID ที่ต้องการ restore
               เช่น: $0 100

Options:
  --latest     Restore backup ล่าสุด
  --file FILE  ระบุไฟล์ backup ที่ต้องการ restore
  --force      ยืนยัน restore โดยไม่ถาม (สำหรับ automation)
  --nostart    ไม่ start LXC หลัง restore
  -h, --help   แสดงการใช้งาน

Examples:
  $0 100                      # Restore LXC 100 จาก backup ล่าสุด
  $0 --file /path/to/backup.tar 100
  $0 --latest --force 100
EOF
    exit 0
}

# ตรวจสอบว่าเป็นตัวเลข
is_number() {
    [[ "$1" =~ ^[0-9]+$ ]]
}

# หา backup ล่าสุด
get_latest_backup() {
    local lxc_id="$1"
    local latest
    latest=$(find "${BACKUP_DIR}" -maxdepth 1 -name "*${LXC_NAME}*id${lxc_id}*_*.tar*" -type f 2>/dev/null | sort -r | head -1)
    echo "$latest"
}

# ตรวจสอบ backup file
validate_backup() {
    local file="$1"
    if [[ ! -f "$file" ]]; then
        log "ERROR" "Backup file not found: ${file}"
        return 1
    fi
    # ตรวจสอบว่าเป็น tar file
    if ! tar -tf "$file" &>/dev/null; then
        log "ERROR" "Invalid backup file (not a valid tar): ${file}"
        return 1
    fi
    return 0
}

# ตรวจสอบว่า LXC ID ว่างหรือถูกใช้แล้ว
check_lxc_id() {
    local lxc_id="$1"
    if ! is_number "$lxc_id"; then
        return 1
    fi
    # ตรวจสอบว่า LXC มีอยู่หรือไม่
    pct status "$lxc_id" &>/dev/null
}

# Restore Container
restore_container() {
    local lxc_id="$1"
    local backup_file="$2"
    local no_start="${3:-false}"

    log "INFO" "=== Restore LXC Container ID: ${lxc_id} ==="
    echo -e "${GREEN}=== Restore LXC Container ID: ${lxc_id} ===${NC}"
    echo "Backup file: ${backup_file}"
    log "INFO" "Backup file: ${backup_file}"

    # ตรวจสอบ backup file
    if ! validate_backup "$backup_file"; then
        echo -e "${RED}❌ Error: Invalid backup file${NC}"
        return 1
    fi

    # ตรวจสอบ LXC ID
    if check_lxc_id "$lxc_id"; then
        local status=$(pct status "$lxc_id" 2>/dev/null | awk '{print $2}')
        log "WARN" "LXC ${lxc_id} already exists (status: ${status})"

        if [[ "$status" == "running" ]]; then
            echo "Stopping LXC ${lxc_id}..."
            log "INFO" "Stopping LXC ${lxc_id}..."
            pct stop "$lxc_id" || true
            sleep 2
        fi

        echo -e "${YELLOW}⚠️  Destroying existing LXC ${lxc_id}...${NC}"
        log "WARN" "Destroying existing LXC ${lxc_id}..."
        pct destroy "$lxc_id" || {
            log "ERROR" "Failed to destroy LXC ${lxc_id}"
            echo -e "${RED}❌ Error: Failed to destroy existing LXC${NC}"
            return 1
        }
    fi

    # Restore จาก backup
    # Proxmox ใช้ pct restore หรือ qm restore สำหรับ LXC
    log "INFO" "Restoring from backup..."
    echo "Restoring from backup..."

    if ! pct restore "$lxc_id" "$backup_file" --storage local 2>> "$LOG_FILE"; then
        log "ERROR" "Failed to restore LXC ${lxc_id}"
        echo -e "${RED}❌ Error: Failed to restore LXC${NC}"
        return 1
    fi

    log "INFO" "Restore completed for LXC ${lxc_id}"
    echo -e "${GREEN}✅ Restore completed successfully!${NC}"

    # Start LXC
    if [[ "$no_start" != "true" ]]; then
        log "INFO" "Starting LXC ${lxc_id}..."
        echo "Starting LXC ${lxc_id}..."

        if pct start "$lxc_id"; then
            log "INFO" "LXC ${lxc_id} started successfully"
            echo -e "${GREEN}✅ LXC ${lxc_id} started${NC}"

            # Health check
            sleep 3
            local status=$(pct status "$lxc_id" 2>/dev/null | awk '{print $2}')
            if [[ "$status" == "running" ]]; then
                log "INFO" "Health check passed: LXC ${lxc_id} is running"
                echo -e "${GREEN}✅ Health check passed${NC}"
            else
                log "WARN" "Health check: LXC ${lxc_id} status is ${status}"
                echo -e "${YELLOW}⚠️  Health check: LXC status is ${status}${NC}"
            fi
        else
            log "ERROR" "Failed to start LXC ${lxc_id}"
            echo -e "${RED}❌ Error: Failed to start LXC${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  Skipping start (--nostart flag)${NC}"
    fi

    return 0
}

# Confirm restore
confirm_restore() {
    local lxc_id="$1"
    local backup_file="$2"

    cat << EOF

${YELLOW}⚠️  WARNING: This is a DESTRUCTIVE operation!${NC}

Details:
  LXC ID:     ${lxc_id}
  Backup:     $(basename "$backup_file")
  Target:     $BACKUP_DIR

This will:
  1. Stop (if running) and DESTROY existing LXC ${lxc_id}
  2. Restore from backup
  3. Start the new LXC

EOF

    if [[ "$FORCE_MODE" == "true" ]]; then
        echo -e "${BLUE}ℹ️  FORCE mode enabled - proceeding without confirmation${NC}"
        return 0
    fi

    read -p "Continue? (yes/no): " -r
    if [[ ! "$REPLY" =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Cancelled."
        return 1
    fi
    return 0
}

# ========================================
# MAIN
# ========================================

# Parse options
TARGET_ID=""
BACKUP_FILE=""
FORCE_MODE=false
NO_START=false
USE_LATEST=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage
            ;;
        --force)
            FORCE_MODE=true
            shift
            ;;
        --nostart)
            NO_START=true
            shift
            ;;
        --latest)
            USE_LATEST=true
            shift
            ;;
        --file)
            BACKUP_FILE="$2"
            shift 2
            ;;
        [0-9]*)
            TARGET_ID="$1"
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            ;;
    esac
done

# ตรวจสอบ prerequisites
if ! command -v pct &>/dev/null; then
    log "ERROR" "pct not found. This script must run on Proxmox VE host."
    echo -e "${RED}❌ Error: pct not found. Run on Proxmox VE host.${NC}"
    exit 1
fi

# Validate LXC ID
if [[ -z "$TARGET_ID" ]] && [[ -n "$LXC_ID" ]]; then
    TARGET_ID="$LXC_ID"
fi

if [[ -z "$TARGET_ID" ]]; then
    echo -e "${RED}❌ Error: Please specify LXC_ID${NC}"
    usage
fi

if ! is_number "$TARGET_ID"; then
    echo -e "${RED}❌ Error: LXC_ID must be a number${NC}"
    exit 1
fi

# Validate backup file
if [[ -z "$BACKUP_FILE" ]]; then
    if [[ "$USE_LATEST" == "true" ]]; then
        BACKUP_FILE=$(get_latest_backup "$TARGET_ID")
        if [[ -z "$BACKUP_FILE" ]]; then
            log "ERROR" "No backup found for LXC ${TARGET_ID}"
            echo -e "${RED}❌ Error: No backup found for LXC ${TARGET_ID}${NC}"
            exit 1
        fi
        log "INFO" "Using latest backup: ${BACKUP_FILE}"
        echo "Using latest backup: $(basename "$BACKUP_FILE")"
    else
        log "ERROR" "No backup file specified. Use --latest or --file"
        echo -e "${RED}❌ Error: Please specify backup file with --latest or --file${NC}"
        usage
    fi
fi

# Confirm
if ! confirm_restore "$TARGET_ID" "$BACKUP_FILE"; then
    log "INFO" "Restore cancelled by user"
    exit 0
fi

# Restore
if restore_container "$TARGET_ID" "$BACKUP_FILE" "$NO_START"; then
    log "INFO" "=== Restore SUCCESS for LXC ${TARGET_ID} ==="
    echo ""
    echo -e "${GREEN}🎉 Restore completed successfully!${NC}"
    echo "Log: ${LOG_FILE}"
    exit 0
else
    log "ERROR" "=== Restore FAILED for LXC ${TARGET_ID} ==="
    echo ""
    echo -e "${RED}❌ Restore failed! Check log: ${LOG_FILE}${NC}"
    exit 1
fi
