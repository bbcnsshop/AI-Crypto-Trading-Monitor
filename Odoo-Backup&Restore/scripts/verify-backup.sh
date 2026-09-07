#!/bin/bash
# verify-backup.sh
# ตรวจสอบความสมบูรณ์ของ backup

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

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging
LOG_DIR="${SCRIPT_DIR}/../logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/verify-$(date +%Y%m%d).log"

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

Verify integrity of LXC backups

Options:
  --file FILE   ตรวจสอบไฟล์ backup ที่ระบุ (ใช้ซ้ำได้หลายครั้ง)
  --id ID       ตรวจสอบ backup ทั้งหมดของ LXC ID
  --all         ตรวจสอบ backup ทั้งหมด
  --verbose     แสดงผลละเอียด
  --checksum    ตรวจสอบด้วย sha256sum
  -h, --help    แสดงการใช้งาน

Examples:
  $0 --all
  $0 --id 100
  $0 --file /path/to/backup.tar
  $0 --all --checksum
EOF
    exit 0
}

# ตรวจสอบว่าเป็น LXC backup filename
is_lxc_backup() {
    local file="$1"
    local filename=$(basename "$file")
    # ใช้ regex เข้มงวด
    [[ "$filename" =~ ^${LXC_NAME}_id[0-9]+_[0-9]{8}_[0-9]{6}\.tar$ ]] || \
    [[ "$filename" =~ ^vzdump-lxc-[0-9]+-[0-9]{8}_[0-9]{6}\.tar$ ]] || \
    [[ "$filename" =~ ^vzdump-lxc-[0-9]+-[0-9]{4}_[0-9]{2}_[0-9]{2}-[0-9]{2}_[0-9]{2}_[0-9]{2}\.tar$ ]]
}

# ตรวจสอบไฟล์ tarball
verify_tarball() {
    local file="$1"
    local verbose="${2:-false}"
    local use_checksum="${3:-false}"

    if [[ "$verbose" == "true" ]]; then
        echo "Verifying: $(basename "$file")"
    fi

    # ตรวจสอบว่า file มีอยู่และไม่ใช่ 0 byte
    if [[ ! -f "$file" ]]; then
        log "ERROR" "File not found: $file"
        echo -e "${RED}❌ File not found: $file${NC}"
        return 1
    fi

    if [[ ! -s "$file" ]]; then
        log "ERROR" "Empty file: $file"
        echo -e "${RED}❌ Empty file: $file${NC}"
        return 1
    fi

    # ตรวจสอบว่าเป็น tar file
    if ! tar -tf "$file" &>/dev/null; then
        log "ERROR" "Invalid tar file: $file"
        echo -e "${RED}❌ ERROR: $(basename "$file") - Invalid or corrupted tar file${NC}"
        return 1
    fi

    # ตรวจสอบ checksum (optional)
    if [[ "$use_checksum" == "true" ]]; then
        local checksum_file="${file}.sha256"
        if [[ -f "$checksum_file" ]]; then
            if ! sha256sum -c "$checksum_file" &>/dev/null; then
                log "ERROR" "Checksum mismatch: $file"
                echo -e "${RED}❌ ERROR: $(basename "$file") - Checksum mismatch${NC}"
                return 1
            fi
        fi
    fi

    if [[ "$verbose" == "true" ]]; then
        log "INFO" "OK: $file"
        echo -e "${GREEN}✅ OK: $(basename "$file")${NC}"
    fi
    return 0
}

# ========================================
# MAIN
# ========================================

# Default values
VERBOSE=false
FIX_MODE=false
USE_CHECKSUM=false
FILES_TO_CHECK=()
LXC_ID_TO_CHECK=""
CHECK_ALL=false

# Parse options
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage
            ;;
        --file)
            if [[ -z "$2" ]]; then
                echo -e "${RED}❌ --file requires a path${NC}"
                exit 1
            fi
            FILES_TO_CHECK+=("$2")
            shift 2
            ;;
        --id)
            if [[ -z "$2" ]]; then
                echo -e "${RED}❌ --id requires an ID${NC}"
                exit 1
            fi
            LXC_ID_TO_CHECK="$2"
            shift 2
            ;;
        --all)
            CHECK_ALL=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --fix)
            FIX_MODE=true
            shift
            ;;
        --checksum)
            USE_CHECKSUM=true
            shift
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
    echo -e "${RED}❌ Backup directory not found: $BACKUP_DIR${NC}"
    exit 1
fi

# Initialize counters
passed=0
failed=0

# Mode 1: ตรวจสอบไฟล์ที่ระบุ
if [[ ${#FILES_TO_CHECK[@]} -gt 0 ]]; then
    log "INFO" "=== Verifying Specific Files ==="
    echo -e "${GREEN}=== Verifying Specific Files ===${NC}"

    for file in "${FILES_TO_CHECK[@]}"; do
        if [[ -f "$file" ]]; then
            if verify_tarball "$file" "$VERBOSE" "$USE_CHECKSUM"; then
                passed=$((passed + 1))
            else
                failed=$((failed + 1))
            fi
        else
            log "ERROR" "File not found: $file"
            echo -e "${RED}❌ File not found: $file${NC}"
            failed=$((failed + 1))
        fi
    done

# Mode 2: ตรวจสอบ backup ทั้งหมดของ LXC ID
elif [[ -n "$LXC_ID_TO_CHECK" ]]; then
    log "INFO" "=== Verifying Backups for LXC ID: ${LXC_ID_TO_CHECK} ==="
    echo -e "${GREEN}=== Verifying Backups for LXC ID: ${LXC_ID_TO_CHECK} ===${NC}"

    # หาไฟล์ด้วย regex ที่เข้มงวด (หลีกเลี่ยง backslash parens ใน process substitution)
    mapfile -t files < <(
        {
            find "${BACKUP_DIR}" -maxdepth 1 -type f -name "${LXC_NAME}_id${LXC_ID_TO_CHECK}_[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9][0-9][0-9].tar" 2>/dev/null
            find "${BACKUP_DIR}" -maxdepth 1 -type f -name "vzdump-lxc-${LXC_ID_TO_CHECK}-*.tar" 2>/dev/null
        } | sort -r
    )

    if [[ ${#files[@]} -eq 0 ]]; then
        log "ERROR" "No backups found for LXC ID ${LXC_ID_TO_CHECK}"
        echo -e "${RED}❌ No backups found for LXC ID ${LXC_ID_TO_CHECK}${NC}"
        exit 1
    fi

    echo "Found ${#files[@]} backup(s)"
    echo ""

    for file in "${files[@]}"; do
        if [[ -n "$file" ]] && [[ -f "$file" ]]; then
            if verify_tarball "$file" "$VERBOSE" "$USE_CHECKSUM"; then
                passed=$((passed + 1))
            else
                failed=$((failed + 1))
            fi
        fi
    done

# Mode 3: ตรวจสอบ backup ทั้งหมด
elif [[ "$CHECK_ALL" == true ]]; then
    log "INFO" "=== Verifying All Backups ==="
    echo -e "${GREEN}=== Verifying All Backups ===${NC}"

    # หาไฟล์ด้วย pattern ที่ปลอดภัย
    mapfile -t files < <(find "${BACKUP_DIR}" -maxdepth 1 -type f -name "*.tar" 2>/dev/null | sort -r)

    if [[ ${#files[@]} -eq 0 ]]; then
        log "ERROR" "No backups found in ${BACKUP_DIR}"
        echo -e "${RED}❌ No backups found in ${BACKUP_DIR}${NC}"
        exit 1
    fi

    echo "Found ${#files[@]} backup file(s)"
    echo ""

    for file in "${files[@]}"; do
        [[ -z "$file" ]] && continue
        # ตรวจสอบว่าเป็น LXC backup หรือไม่ (ถ้าไม่ใช่ก็ข้าม)
        if is_lxc_backup "$file"; then
            if verify_tarball "$file" "$VERBOSE" "$USE_CHECKSUM"; then
                passed=$((passed + 1))
            else
                failed=$((failed + 1))
            fi
        fi
    done

# ไม่ได้ระบุ mode
else
    usage
fi

# Summary
echo ""
echo "=== Result ==="
echo -e "${GREEN}✅ Passed: ${passed}${NC}"
if [[ $failed -gt 0 ]]; then
    echo -e "${RED}❌ Failed: ${failed}${NC}"
else
    echo -e "${GREEN}❌ Failed: 0${NC}"
fi

log "INFO" "Verification complete: ${passed} passed, ${failed} failed"

# Fix mode
if [[ "$FIX_MODE" == true ]] && [[ "$failed" -gt 0 ]]; then
    echo ""
    echo -e "${YELLOW}⚠️  Fix mode is enabled but automatic repair is not implemented.${NC}"
    echo "   Please manually remove corrupted backups:"
    echo "   ./scripts/cleanup-old-backups.sh --dry-run"
fi

exit $((failed > 0 ? 1 : 0))
