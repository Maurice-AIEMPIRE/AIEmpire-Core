#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/Users/maurice/Documents/Dokumente – Mac mini von Maurice/New project"
OUT_DIR="$REPO_DIR/reports/daily_sprints"
OUT_LINK="$OUT_DIR/latest.md"
TODAY="$(date +%F)"
NOW="$(date '+%Y-%m-%d %H:%M:%S %Z')"
DAY_NAME="$(date '+%A')"

CHANNEL="${SPRINT_CHANNEL:-YouTube}"
POSITIONING="${SPRINT_POSITIONING:-Philosophie x AI}"
OFFER="${SPRINT_OFFER:-AI Clarity Sprint}"

mkdir -p "$OUT_DIR"

HOOK_1="AI macht dich nicht klueger. AI macht dein Denken sichtbar."
HOOK_2="Du brauchst kein neues Tool. Du brauchst bessere Fragen."
HOOK_3="Philosophie ist im AI-Zeitalter kein Luxus, sondern Profit-Hebel."
HOOK_4="Wer mit AI arbeitet, ohne Denkmodell, beschleunigt nur Fehler."

HOOKS=("$HOOK_1" "$HOOK_2" "$HOOK_3" "$HOOK_4")
DAY_OF_YEAR="$(date +%j)"
HOOK_INDEX=$((10#$DAY_OF_YEAR % ${#HOOKS[@]}))
SELECTED_HOOK="${HOOKS[$HOOK_INDEX]}"

CHANNEL_SLUG="$(printf '%s' "$CHANNEL" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-*//;s/-*$//')"
OUT_FILE="$OUT_DIR/${TODAY}_${CHANNEL_SLUG}_sprint.md"

cat > "$OUT_FILE" <<EOF
# Daily Content Sprint - $TODAY ($DAY_NAME)

## Focus
- Channel: $CHANNEL
- Positioning: $POSITIONING
- Offer to mention: $OFFER
- Generated at: $NOW

## Primary Hook
$SELECTED_HOOK

## Sequence Plan (low-load, no parallel work)
1. 08:00-08:20 - Topic lock and angle decision
2. 08:20-09:00 - Script draft (Hook -> Problem -> 3 Models -> Action -> CTA)
3. 09:00-10:00 - Record and edit one long video
4. 10:00-10:25 - Cut one short from same source
5. 10:25-10:45 - Title, thumbnail text, description, CTA links
6. 11:00 - Publish and post one X teaser

## Video Blueprint (6-10 minutes)
1. Hook (0:00-0:20): state contradiction and promise
2. Problem (0:20-1:30): why people fail with AI despite more tools
3. Model 1 (1:30-3:00): clarity before prompts
4. Model 2 (3:00-4:30): constraints create better outputs
5. Model 3 (4:30-6:00): execution beats idea quantity
6. Action (6:00-7:00): 3-line prompt routine for today
7. CTA (last 20s): invite DM/comment with "CLARITY"

## Ready-to-use Assets
- Title candidate: Du nutzt AI falsch: Der philosophische Fix in 7 Minuten
- Thumbnail text: AI + Denken = Umsatz
- X teaser: "Die meisten optimieren Tools. Gewinner optimieren Denkmodelle. Neues Video live."

## KPI Targets
- 24h: CTR >= 5%, retention >= 35%, 3 qualifizierte DMs/Kommentare
- 7d: 1 zahlungsbereites Erstgespraech aus Content

## End-of-day Review
1. Welche Hook hat die meiste Watchtime gebracht?
2. Wo gab es Drop-offs?
3. Was wird morgen exakt wiederverwendet?
EOF

cp "$OUT_FILE" "$OUT_LINK"
printf 'Daily sprint written: %s\n' "$OUT_FILE"
