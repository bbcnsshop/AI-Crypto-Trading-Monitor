#!/bin/bash
# list-backups.sh
# แสดงรายการ backup ทั้งหมด

# ❌ ห้ามใช้ set -e เพราะ find อาจ return 1 เมื่อไม่เจอไฟล์
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
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ========================================
# FUNCTIONS
# ========================================

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

List LXC backups with details

Options:
  --id ID       แสดงเฉพาะ backup ของ LXC ID นี้
  --latest N    แสดงเฉพาะ N backup ล่าสุด (default: 10)
  --sort SIZE|DATE เรียงตามขนาด หรือวันที่ (default: DATE)
  --json        แสดงผลเป็น JSON
  --summary     แสดงเฉพาะสรุป
  -h, --help    แสดงการใช้งาน

Examples:
  $0
  $0 --id 100
  $0 --latest 5 --sort SIZE
EOF
    exit 0
}

# ตรวจสอบว่าเป็น LXC backup filename
is_lxc_backup() {
    local filename="$1"
    [[ "$filename" =~ ^${LXC_NAME}_id[0-9]+_[0-9]{8}_[0-9]{6}\.tar$ ]] || \
    [[ "$filename" =~ ^vzdump-lxc-[0-9]+-[0-9]{8}_[0-9]{6}\.tar$ ]] || \
    [[ "$filename" =~ ^vzdump-lxc-[0-9]+-[0-9]{4}_[0-9]{2}_[0-9]{2}-[0-9]{2}_[0-9]{2}_[0-9]{2}\.tar$ ]]
}

# ดึง LXC ID จาก filename
extract_lxc_id() {
    local filename="$1"
    # ลองหลาย pattern
    echo "$filename" | grep -oE 'id([0-9]+)' | head -1 | sed 's/id//'
}

# ดึงวันที่จาก filename
extract_date() {
    local filename="$1"
    # รูปแบบ: _YYYYMMDD_HHMMSS
    echo "$filename" | grep -oE '_[0-9]{8}_[0-9]{6}' | head -1 | sed 's/_//'
}

# คำนวณอายุ (วัน)
calculate_age_days() {
    local filename="$1"
    local file_date_str=$(extract_date "$filename")

    if [[ -z "$file_date_str" ]] || [[ ! "$file_date_str" =~ ^[0-9]{8}_[0-9]{6}$ ]]; then
        echo "?"
        return
    fi

    local file_timestamp
    if date -d "${file_date_str:0:8} ${file_date_str:9:2}:${file_date_str:11:2}:${file_date_str:13:2}" +%s &>/dev/null; then
        file_timestamp=$(date -d "${file_date_str:0:8} ${file_date_str:9:2}:${file_date_str:11:2}:${file_date_str:13:2}" +%s)
    else
        file_timestamp=$(gdate -j -f "%Y%m%d_%H%M%S" "$file_date_str" +%s 2>/dev/null || echo "")
    fi

    if [[ -n "$file_timestamp" ]]; then
        local now=$(date +%s)
        local age_seconds=$((now - file_timestamp))
        local age_days=$((age_seconds / 86400))
        echo "$age_days"
    else
        echo "?"
    fi
}

# แสดงผลเป็น JSON
print_json() {
    local backup_dir="$1"
    local filter_id="$2"

    echo "{"
    echo "  \"backup_dir\": \"$backup_dir\","
    echo "  \"backups\": ["

    local first=true
    while IFS= read -r file; do
        [[ -z "$file" ]] && continue
        [[ ! -f "$file" ]] && continue

        local filename=$(basename "$file")
        is_lxc_backup "$filename" || continue

        local lxc_id=$(extract_lxc_id "$filename")
        if [[ -n "$filter_id" ]] && [[ "$lxc_id" != "$filter_id" ]]; then
            continue
        fi

        local size=$(du -h "$file" | awk '{print $1}')
        local date_str=$(extract_date "$filename")
        local age=$(calculate_age_days "$filename")

        if [[ "$first" == "true" ]]; then
            first=false
        else
            echo ","
        fi

        cat << JSONEOF
    {
      "filename": "$filename",
      "lxc_id": "$lxc_id",
      "size": "$size",
      "date": "$date_str",
      "age_days": $age,
      "path": "$file"
    }
JSONEOF
    done < <(find "$backup_dir" -maxdepth 1 -name "*.tar" -type f 2>/dev/null | sort -r)

    echo ""
    echo "  ]"
    echo "}"
}

# ========================================
# MAIN
# ========================================

# Default values
FILTER_ID=""
LATEST=""
SORT_BY="DATE"
JSON_OUTPUT=false
SUMMARY_ONLY=false

# Parse options
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage
            ;;
        --id)
            FILTER_ID="$2"
            shift 2
            ;;
        --latest)
            LATEST="$2"
            shift 2
            ;;
        --sort)
            SORT_BY="$2"
            shift 2
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --summary)
            SUMMARY_ONLY=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            ;;
    esac
done

LATEST="${LATEST:-0}"

# ตรวจสอบ backup directory
if [[ ! -d "$BACKUP_DIR" ]]; then
    echo -e "${RED}❌ Backup directory not found: $BACKUP_DIR${NC}"
    exit 1
fi

# JSON mode
if [[ "$JSON_OUTPUT" == "true" ]]; then
    print_json "$BACKUP_DIR" "$FILTER_ID"
    exit 0
fi

# เก็บไฟล์ใน array แทน pipe
mapfile -t all_backups < <(find "$BACKUP_DIR" -maxdepth 1 -name "*.tar" -type f 2>/dev/null)

# Filter และ sort
backups=()
for file in "${all_backups[@]}"; do
    [[ -z "$file" ]] && continue
    [[ ! -f "$file" ]] && continue

    local filename=$(basename "$file")
    is_lxc_backup "$filename" || continue

    local lxc_id=$(extract_lxc_id "$filename")
    if [[ -n "$FILTER_ID" ]] && [[ "$lxc_id" != "$FILTER_ID" ]]; then
        continue
    fi

    backups+=("$file")
done

# Sort
if [[ "$SORT_BY" == "SIZE" ]]; then
    # Sort by size (largest first) - ใช้ temporary file
    printf '%s\n' "${backups[@]}" | while IFS= read -r f; do
        [[ -n "$f" ]] && du "$f" 2>/dev/null
    done | sort -rh | awk '{print $2}' > /tmp/sorted_backups.txt
    mapfile -t backups < /tmp/sorted_backups.txt
    rm -f /tmp/sorted_backups.txt
fi

# Limit
if [[ "$LATEST" -gt 0 ]]; then
    backups=("${backups[@]:0:$LATEST}")
fi

# Count
total=${#backups[@]}
total_size=$(du -ch "${backups[@]}" 2>/dev/null | tail -1 | awk '{print $1}')

# Header
echo -e "${GREEN}=== Backup List ===${NC}"
echo "Directory: ${BACKUP_DIR}"
if [[ -n "$FILTER_ID" ]]; then
    echo "Filter: LXC ID ${FILTER_ID}"
fi
echo ""

if [[ $total -eq 0 ]]; then
    echo -e "${YELLOW}No backups found.${NC}"
    exit 0
fi

# Summary mode
if [[ "$SUMMARY_ONLY" == "true" ]]; then
    echo "Total backups: $total"
    echo "Total size: $total_size"
    exit 0
fi

# แสดงรายละเอียด
echo -e "${CYAN}┌─────────────────────────────────────────────────────────────┐${NC}"
printf "${CYAN}│${NC} %-12s %-8s %-10s %-6s %s\n" "DATE" "LXC ID" "SIZE" "AGE" "FILENAME"
echo -e "${CYAN}├─────────────────────────────────────────────────────────────┤${NC}"

for file in "${backups[@]}"; do
    [[ -z "$file" ]] && continue
    [[ ! -f "$file" ]] && continue

    local filename=$(basename "$file")
    local lxc_id=$(extract_lxc_id "$filename")
    local size=$(du -h "$file" 2>/dev/null | awk '{print $1}')
    local date_str=$(extract_date "$filename")
    local age=$(calculate_age_days "$filename")

    # Format date
    if [[ "$date_str" =~ ^([0-9]{8})_([0-9]{6})$ ]]; then
        local formatted_date="${BASH_REMATCH[1]:0:4}-${BASH_REMATCH[1]:4:2}-${BASH_REMATCH[1]:6:2}"
    else
        local formatted_date="????-??-??"
    fi

    # Color age
    local age_color="$NC"
    if [[ "$age" != "?" ]]; then
        if [[ "$age" -gt 7 ]]; then
            age_color="$YELLOW"
        fi
        if [[ "$age" -gt 30 ]]; then
            age_color="$RED"
        fi
    fi

    printf "${CYAN}│${NC} %-12s ${BLUE}%-8s${NC} %-10s ${age_color}%-6s${NC} %s\n" \
        "$formatted_date" "$lxc_id" "$size" "${age}d" "$filename"
done

echo -e "${CYAN}└─────────────────────────────────────────────────────────────┘${NC}"
echo ""
echo -e "${GREEN}Total: $total backup(s)${NC} | ${GREEN}Total size: $total_size${NC}"

exit 0
