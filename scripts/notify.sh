#!/bin/bash
# AI Empire - Notification System
set -euo pipefail

LOG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/logs"
mkdir -p "${LOG_DIR}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

send_notification() {
    local type=$1 title=$2 message=$3
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')

    case $type in
        success) echo -e "${GREEN}[OK]${NC} $title: $message" ;;
        warning) echo -e "${YELLOW}[!!]${NC} $title: $message" ;;
        error)   echo -e "${RED}[XX]${NC} $title: $message" ;;
        info)    echo -e "${BLUE}[--]${NC} $title: $message" ;;
    esac

    echo "[$timestamp] [$type] $title: $message" >> "${LOG_DIR}/notifications.log"
}

send_notification "${1:-info}" "${2:-Notification}" "${3:-Empire event}"
