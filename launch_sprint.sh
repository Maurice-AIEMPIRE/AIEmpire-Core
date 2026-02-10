#!/bin/bash
echo "🚀 LAUNCHING 500€ REVENUE SPRINT..."

# Make scripts executable
chmod +x massive_offensive.py
chmod +x guerilla_growth.py
chmod +x revenue_dashboard.py

# Open Instructions and Offer
open SPRINT_INSTRUCTIONS.md
open OFFER_500_EURO_SPRINT.md

# Open Dashboard in a new terminal window
osascript -e 'tell application "Terminal" to do script "cd \"'$(pwd)'\" && python3 revenue_dashboard.py"'

echo "✅ DASHBOARD LAUNCHED."
echo "⚠️  CHECK 'MASSIVE_MARKETING_BLITZ.md' WHEN GENERATION IS COMPLETE."
