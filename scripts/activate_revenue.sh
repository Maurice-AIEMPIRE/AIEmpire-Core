#!/bin/bash
# ============================================================
# Revenue Channel Activation Script
# ============================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║       Revenue Channels Activation — AIEmpire-Core       ║"
echo "║       Target: EUR 100,000/Monat (1-3 Jahre)             ║"
echo "╚══════════════════════════════════════════════════════════╝"

echo ""
echo "[1] GUMROAD — Digital Products Setup"
echo "  → BMA Checklisten (EUR 27 x 9 = EUR 243/Mo)"
echo "  → AI Agent Kits (EUR 49 x 3 = EUR 147/Mo)"
echo "  → Status: Ready for upload"
echo ""
echo "  Action: Create product pages on Gumroad"
echo "  Files: $PROJECT_ROOT/BMA_ACADEMY/"
echo "  Files: $PROJECT_ROOT/products/"

echo ""
echo "[2] FIVERR — Service Gigs"
echo "  → AI Agent Development (EUR 100-5000)"
echo "  → BMA System Implementation (EUR 500-10000)"  
echo "  → Custom AI Training (EUR 150-2000)"
echo "  Status: Ready for listing"

echo ""
echo "[3] CONSULTING — Direct Sales"
echo "  → BMA + AI Integration (EUR 2000-10000/Projekt)"
echo "  → Target: 5 BMA companies/month"
echo "  Status: Lead database ready"

echo ""
echo "[4] COMMUNITY — Discord Premium"
echo "  → Agent Builders Club (EUR 29/Monat)"
echo "  → 1000 members = EUR 29,000/Monat"
echo "  Status: Community template ready"

echo ""
echo "[5] X/TWITTER — Content + Lead Gen"
echo "  → 3 Personas, 9 Posts/Day"
echo "  → Lead generation integration"
echo "  Status: Content calendar ready"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║              ACTIVATION CHECKLIST                        ║"
echo "╠══════════════════════════════════════════════════════════╣"

checklist=(
    "☐ Create Gumroad account + verify payment"
    "☐ Upload 9 BMA Checklisten (EUR 27)"
    "☐ Create 3 Fiverr gigs with samples"
    "☐ Set up BMA sales landing page"
    "☐ Configure Twitter automation (3 personas)"
    "☐ Set up Zapier/Make integrations"
    "☐ Create Discord community + pricing"
    "☐ Configure CRM for lead tracking"
    "☐ Run first content cycle"
    "☐ Monitor revenue (daily: empire_engine.py revenue)"
)

for item in "${checklist[@]}"; do
    echo "║ $item"
done

echo "╚══════════════════════════════════════════════════════════╝"

echo ""
echo "Next steps:"
echo "  1. python3 empire_engine.py produce       # Generate content"
echo "  2. python3 empire_engine.py distribute    # Post to channels"
echo "  3. python3 empire_engine.py leads         # Process leads"
echo "  4. python3 empire_engine.py revenue       # Track revenue"
