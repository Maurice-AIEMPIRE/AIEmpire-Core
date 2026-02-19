#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
# CRON SETUP — AIEmpire-Core Content Automation
# ══════════════════════════════════════════════════════════════════════════════
#
# Installiert alle Cron Jobs fuer automatische Content-Generierung,
# Revenue-Tracking und System-Health-Checks.
#
# Diese Jobs ersetzen die GitHub Actions Workflows auf dem Server
# → Kostenlos, schneller, kein Minuten-Limit.
#
# Usage:
#   chmod +x scripts/cron_setup.sh
#   sudo ./scripts/cron_setup.sh
#
# ══════════════════════════════════════════════════════════════════════════════

set -e

G='\033[0;32m'
Y='\033[1;33m'
B='\033[0;34m'
W='\033[1;37m'
N='\033[0m'

PROJECT_DIR="${AIEMPIRE_DIR:-/opt/aiempire}"
LOG_DIR="/var/log/aiempire"

echo ""
echo -e "${W}╔═══════════════════════════════════════════════════════════╗${N}"
echo -e "${W}║      CRON SETUP — Content Automation Engine              ║${N}"
echo -e "${W}╚═══════════════════════════════════════════════════════════╝${N}"
echo ""

# Create log directory
mkdir -p "$LOG_DIR"

# Create the crontab entries
CRON_FILE="/tmp/aiempire_cron"

cat > "$CRON_FILE" << CRON
# ══════════════════════════════════════════════════════════════════════════════
# AIEmpire-Core — Automatische Content + Revenue Engine
# Installiert: $(date +%Y-%m-%d)
# ══════════════════════════════════════════════════════════════════════════════

# Umgebungsvariablen
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
AIEMPIRE_DIR=${PROJECT_DIR}

# ─── CONTENT GENERATION ─────────────────────────────────────────────────────
# Morgens 08:00 DE (06:00 UTC) — Tages-Content generieren
0 6 * * * cd ${PROJECT_DIR} && python3 src/content_scheduler.py >> ${LOG_DIR}/content.log 2>&1

# Mittags 12:00 DE (10:00 UTC) — Nachmittags-Content
0 10 * * * cd ${PROJECT_DIR} && python3 src/content_scheduler.py >> ${LOG_DIR}/content.log 2>&1

# Abends 18:00 DE (16:00 UTC) — Abend-Content + Engagement
0 16 * * * cd ${PROJECT_DIR} && python3 src/content_scheduler.py >> ${LOG_DIR}/content.log 2>&1

# ─── EMPIRE ENGINE ───────────────────────────────────────────────────────────
# Alle 4 Stunden — Vollstaendiger Auto-Zyklus
0 */4 * * * cd ${PROJECT_DIR} && python3 empire_engine.py auto >> ${LOG_DIR}/engine.log 2>&1

# ─── REVENUE TRACKING ───────────────────────────────────────────────────────
# Taeglich 22:00 DE (20:00 UTC) — Revenue Report
0 20 * * * cd ${PROJECT_DIR} && python3 empire_engine.py revenue >> ${LOG_DIR}/revenue.log 2>&1

# ─── HEALTH CHECKS ──────────────────────────────────────────────────────────
# Alle 15 Minuten — System-Health
*/15 * * * * cd ${PROJECT_DIR} && python3 workflow_system/resource_guard.py >> ${LOG_DIR}/health.log 2>&1

# ─── LOG ROTATION ────────────────────────────────────────────────────────────
# Woechtentlich Sonntag 03:00 — Alte Logs komprimieren
0 3 * * 0 find ${LOG_DIR} -name "*.log" -size +10M -exec gzip {} \;

# ─── WEEKLY REVIEW ───────────────────────────────────────────────────────────
# Sonntag 10:00 DE (08:00 UTC) — Wochenreview
0 8 * * 0 cd ${PROJECT_DIR} && python3 empire_engine.py revenue >> ${LOG_DIR}/weekly_review.log 2>&1
CRON

# Install crontab (keep existing entries)
if crontab -l 2>/dev/null | grep -q "AIEmpire"; then
    echo -e "${Y}[INFO]${N} Bestehende AIEmpire Cron Jobs gefunden — aktualisiere..."
    # Remove old AIEmpire entries and add new ones
    crontab -l 2>/dev/null | grep -v "AIEmpire\|aiempire\|empire_engine\|content_scheduler\|resource_guard" > /tmp/existing_cron || true
    cat /tmp/existing_cron "$CRON_FILE" | crontab -
else
    echo -e "${B}[INFO]${N} Installiere AIEmpire Cron Jobs..."
    (crontab -l 2>/dev/null; cat "$CRON_FILE") | crontab -
fi

rm -f "$CRON_FILE" /tmp/existing_cron

echo ""
echo -e "${G}[OK]${N} Cron Jobs installiert!"
echo ""
echo -e "  ${W}Installierte Jobs:${N}"
echo -e "  ${B}06:00 UTC${N} Content-Generierung (morgens)"
echo -e "  ${B}10:00 UTC${N} Content-Generierung (mittags)"
echo -e "  ${B}16:00 UTC${N} Content-Generierung (abends)"
echo -e "  ${B}*/4h   ${N} Empire Engine Auto-Zyklus"
echo -e "  ${B}20:00 UTC${N} Revenue Report"
echo -e "  ${B}*/15min ${N} Health Check"
echo -e "  ${B}So 08:00${N} Wochenreview"
echo ""
echo -e "  ${W}Logs:${N} ${LOG_DIR}/"
echo -e "  ${W}Pruefen:${N} crontab -l"
echo ""
