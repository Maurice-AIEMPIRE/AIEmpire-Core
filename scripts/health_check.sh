#!/bin/bash

###############################################################################
# Health Check Script - Maurice's AI Empire
#
# Purpose: Quick system health check for all critical services
# Exit Code: 0 = All services UP, 1 = Any service DOWN
#
# Usage:
#   ./health_check.sh                    # Run all checks
#   ./health_check.sh --verbose          # Show details
#   ./health_check.sh --json             # JSON output
#
# Integration:
#   * Use in cron jobs for monitoring
#   * Use in CI/CD pipelines
#   * Feed results to external monitoring systems
#
# Cron Example:
#   */5 * * * * /path/to/health_check.sh --json >> /var/log/empire-health.log
#
###############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RESET='\033[0m'

# Configuration
VERBOSE=${VERBOSE:-0}
JSON_OUTPUT=${JSON_OUTPUT:-0}
TIMEOUT=3

# Service configuration
declare -A SERVICES=(
    ["n8n"]="localhost:5678"
    ["Redis"]="localhost:6379"
    ["PostgreSQL"]="localhost:5432"
    ["Ollama"]="localhost:11434"
    ["OpenClaw"]="localhost:18789"
)

# Track results
SERVICES_UP=0
SERVICES_DOWN=0
declare -A RESULTS
declare -a DOWN_SERVICES

###############################################################################
# Helper Functions
###############################################################################

log_verbose() {
    if [[ $VERBOSE -eq 1 ]]; then
        echo "[INFO] $*" >&2
    fi
}

log_error() {
    echo "[ERROR] $*" >&2
}

# Check if a port is open via TCP socket
check_port() {
    local host="$1"
    local port="$2"
    local timeout="$3"

    if command -v timeout &> /dev/null; then
        timeout "$timeout" bash -c "cat < /dev/null > /dev/tcp/$host/$port" 2>/dev/null
    else
        # Fallback using netcat if timeout not available
        if command -v nc &> /dev/null; then
            nc -z -w "$timeout" "$host" "$port" 2>/dev/null
        else
            # Final fallback: use python
            python3 -c "
import socket
import sys
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout($timeout)
try:
    sock.connect(('$host', $port))
    sock.close()
    sys.exit(0)
except:
    sys.exit(1)
" 2>/dev/null
        fi
    fi
}

# Check HTTP service with headers
check_http() {
    local host="$1"
    local port="$2"
    local path="${3:-/health}"

    if command -v curl &> /dev/null; then
        local response
        response=$(curl -s -m "$TIMEOUT" -o /dev/null -w "%{http_code}" "http://$host:$port$path" 2>/dev/null || echo "000")
        if [[ "$response" =~ ^[23][0-9]{2}$ ]]; then
            return 0
        else
            return 1
        fi
    else
        # Fallback to TCP check if curl not available
        check_port "$host" "$port" "$TIMEOUT"
    fi
}

# Check individual service
check_service() {
    local service_name="$1"
    local host_port="$2"
    local protocol="${3:-tcp}"

    IFS=':' read -r host port <<< "$host_port"

    log_verbose "Checking $service_name ($host:$port) via $protocol..."

    if [[ "$protocol" == "http" ]]; then
        if check_http "$host" "$port"; then
            RESULTS[$service_name]="UP"
            ((SERVICES_UP++))
            return 0
        else
            RESULTS[$service_name]="DOWN"
            DOWN_SERVICES+=("$service_name")
            ((SERVICES_DOWN++))
            return 1
        fi
    else
        # TCP check
        if check_port "$host" "$port" "$TIMEOUT"; then
            RESULTS[$service_name]="UP"
            ((SERVICES_UP++))
            return 0
        else
            RESULTS[$service_name]="DOWN"
            DOWN_SERVICES+=("$service_name")
            ((SERVICES_DOWN++))
            return 1
        fi
    fi
}

# Print formatted output
print_results() {
    if [[ $JSON_OUTPUT -eq 1 ]]; then
        print_json_results
    else
        print_text_results
    fi
}

print_text_results() {
    echo -e "${BLUE}════════════════════════════════════════════════════════${RESET}"
    echo -e "${BLUE}System Health Check - $(date '+%Y-%m-%d %H:%M:%S')${RESET}"
    echo -e "${BLUE}════════════════════════════════════════════════════════${RESET}"
    echo ""

    for service in "${!SERVICES[@]}"; do
        local status="${RESULTS[$service]}"
        if [[ "$status" == "UP" ]]; then
            echo -e "  ${GREEN}✓${RESET} $service: ${GREEN}UP${RESET}"
        else
            echo -e "  ${RED}✗${RESET} $service: ${RED}DOWN${RESET}"
        fi
    done

    echo ""
    echo -e "Summary: ${GREEN}$SERVICES_UP UP${RESET} | ${RED}$SERVICES_DOWN DOWN${RESET}"
    echo ""

    if [[ $SERVICES_DOWN -gt 0 ]]; then
        echo -e "${RED}⚠ Critical Services Down:${RESET}"
        for service in "${DOWN_SERVICES[@]}"; do
            echo -e "  - $service"
        done
        echo ""
    fi
}

print_json_results() {
    local timestamp
    timestamp=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

    echo "{"
    echo "  \"timestamp\": \"$timestamp\","
    echo "  \"summary\": {"
    echo "    \"up\": $SERVICES_UP,"
    echo "    \"down\": $SERVICES_DOWN,"
    echo "    \"total\": $((SERVICES_UP + SERVICES_DOWN))"
    echo "  },"
    echo "  \"services\": {"

    local first=1
    for service in "${!SERVICES[@]}"; do
        if [[ $first -eq 0 ]]; then
            echo ","
        fi
        local status="${RESULTS[$service]}"
        echo -n "    \"$service\": {\"status\": \"$status\"}"
        first=0
    done

    echo ""
    echo "  },"
    echo "  \"exit_code\": $([[ $SERVICES_DOWN -gt 0 ]] && echo 1 || echo 0)"
    echo "}"
}

###############################################################################
# Argument Parsing
###############################################################################

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -v|--verbose)
                VERBOSE=1
                shift
                ;;
            -j|--json)
                JSON_OUTPUT=1
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

show_help() {
    cat << EOF
Health Check Script - Maurice's AI Empire

Usage: $0 [OPTIONS]

Options:
    -v, --verbose    Show detailed output for each check
    -j, --json       Output results as JSON
    -h, --help       Show this help message

Exit Codes:
    0 = All services UP
    1 = One or more services DOWN

Examples:
    # Run standard check
    $0

    # Show verbose output
    $0 --verbose

    # JSON output for automation
    $0 --json

    # Combine options
    $0 --verbose --json

Environment Variables:
    VERBOSE=1       Enable verbose mode
    JSON_OUTPUT=1   Enable JSON output
    TIMEOUT=N       Change timeout in seconds (default: 3)

Integration:
    # Add to crontab for periodic monitoring
    */5 * * * * ${TIMEOUT:-3} /path/to/health_check.sh --json >> /var/log/health.log

    # Use in monitoring systems
    prometheus_node_exporter_textfile_collector_dir=/path/
    $0 --json | jq . >> /var/lib/node_exporter/textfile_collector/health.json

EOF
}

###############################################################################
# Main Execution
###############################################################################

main() {
    parse_args "$@"

    log_verbose "Starting health checks..."
    log_verbose "Timeout: ${TIMEOUT}s"

    # Check each service
    for service in "${!SERVICES[@]}"; do
        host_port="${SERVICES[$service]}"

        # Determine protocol based on port
        port="${host_port##*:}"
        protocol="tcp"

        case "$port" in
            5678|18789|11434)  # n8n, OpenClaw, Ollama
                protocol="http"
                ;;
            6379|5432)  # Redis, PostgreSQL
                protocol="tcp"
                ;;
        esac

        check_service "$service" "$host_port" "$protocol" || true
    done

    # Print results
    print_results

    # Exit with appropriate code
    if [[ $SERVICES_DOWN -gt 0 ]]; then
        exit 1
    else
        exit 0
    fi
}

# Execute main
main "$@"
