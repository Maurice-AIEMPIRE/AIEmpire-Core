#!/bin/bash
# collect_reports.sh – Wrapper to run the Python report collector
# Usage: bash antigravity/scripts/collect_reports.sh
set -e
cd "$(dirname "$0")/../.."
echo "⚡ Antigravity Report Collector"
echo "================================"
python3 antigravity/collect_reports.py
echo ""
echo "Done. Reports saved to antigravity/_reports/"
