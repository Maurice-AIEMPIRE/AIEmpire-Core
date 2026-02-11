#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="${SPRINT_BASE_DIR:-$HOME/Library/Application Support/ai-empire}"
OUT_DIR="$BASE_DIR/daily_sprints"
OUT_LINK="$OUT_DIR/latest.md"
ENV_FILE="$BASE_DIR/daily_content_sprint.env"
LOCK_DIR="$BASE_DIR/.daily_content_sprint.lock"

mkdir -p "$OUT_DIR"

if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "Daily sprint already running, skipping."
  exit 0
fi

cleanup() {
  rmdir "$LOCK_DIR" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

default_channel_for_day() {
  case "$1" in
    1) printf '%s\n' "${MONDAY_CHANNEL:-YouTube}" ;;
    2) printf '%s\n' "${TUESDAY_CHANNEL:-X}" ;;
    3) printf '%s\n' "${WEDNESDAY_CHANNEL:-YouTube Shorts}" ;;
    4) printf '%s\n' "${THURSDAY_CHANNEL:-X}" ;;
    5) printf '%s\n' "${FRIDAY_CHANNEL:-YouTube}" ;;
    6) printf '%s\n' "${SATURDAY_CHANNEL:-X}" ;;
    7) printf '%s\n' "${SUNDAY_CHANNEL:-Strategy}" ;;
    *) printf '%s\n' "YouTube" ;;
  esac
}

TODAY="$(date +%F)"
NOW="$(date '+%Y-%m-%d %H:%M:%S %Z')"
DAY_NAME="$(date '+%A')"
DAY_NUM="$(date +%u)"

CHANNEL="${SPRINT_CHANNEL:-$(default_channel_for_day "$DAY_NUM")}"
POSITIONING="${SPRINT_POSITIONING:-Philosophie x AI}"
OFFER="${SPRINT_OFFER:-AI Clarity Sprint}"
CTA_KEYWORD="${SPRINT_CTA_KEYWORD:-CLARITY}"

HOOK_1="AI macht dich nicht klueger. AI macht dein Denken sichtbar."
HOOK_2="Du brauchst kein neues Tool. Du brauchst bessere Fragen."
HOOK_3="Philosophie ist im AI-Zeitalter kein Luxus, sondern Profit-Hebel."
HOOK_4="Wer mit AI arbeitet, ohne Denkmodell, beschleunigt nur Fehler."

HOOKS=("$HOOK_1" "$HOOK_2" "$HOOK_3" "$HOOK_4")
DAY_OF_YEAR="$(date +%j)"
HOOK_INDEX=$((10#$DAY_OF_YEAR % ${#HOOKS[@]}))
SELECTED_HOOK="${HOOKS[$HOOK_INDEX]}"

SEQUENCE_PLAN="$(cat <<'EOF'
## Sequence Plan (low-load, no parallel work)
1. 08:00-08:20 - Topic lock and angle decision
2. 08:20-09:00 - Script draft and framework
3. 09:00-10:00 - Production of one primary asset
4. 10:00-10:25 - One repurpose asset from same source
5. 10:25-10:45 - Packaging (title/copy/thumbnail or hook)
6. 11:00 - Publish and one distribution post
EOF
)"

CHANNEL_BLOCK=""
PRIMARY_TITLE=""
CREATIVE_CUE=""
DISTRIBUTION_TEASER=""
KPI_24H=""
KPI_7D=""

CHANNEL_LOWER="$(printf '%s' "$CHANNEL" | tr '[:upper:]' '[:lower:]')"

case "$CHANNEL_LOWER" in
  "youtube")
    CHANNEL_BLOCK="$(cat <<EOF
## Channel Blueprint (YouTube)
1. Hook (0:00-0:20): contradiction and promise
2. Problem (0:20-1:30): why people fail with AI despite more tools
3. Model 1 (1:30-3:00): clarity before prompts
4. Model 2 (3:00-4:30): constraints create better outputs
5. Model 3 (4:30-6:00): execution beats idea quantity
6. Action (6:00-7:00): daily 3-line routine
7. CTA (last 20s): comment or DM "$CTA_KEYWORD"
EOF
)"
    PRIMARY_TITLE="Du nutzt AI falsch: Der philosophische Fix in 7 Minuten"
    CREATIVE_CUE="Thumbnail text: AI + Denken = Umsatz"
    DISTRIBUTION_TEASER="Die meisten optimieren Tools. Gewinner optimieren Denkmodelle. Neues Video live."
    KPI_24H="CTR >= 5%, retention >= 35%, 3 qualifizierte DMs/Kommentare"
    KPI_7D="1 zahlungsbereites Erstgespraech aus Content"
    ;;
  "youtube shorts"|"shorts")
    CHANNEL_BLOCK="$(cat <<EOF
## Channel Blueprint (YouTube Shorts)
1. 0-2s: harte These als Pattern Break
2. 2-12s: ein Denkfehler + Konsequenz
3. 12-30s: ein konkreter Fix
4. 30-45s: CTA mit "$CTA_KEYWORD"
EOF
)"
    PRIMARY_TITLE="30 Sekunden Denkmodell fuer bessere AI-Outputs"
    CREATIVE_CUE="On-screen text: Klarheit vor Prompt"
    DISTRIBUTION_TEASER="Kurzer Fix fuer bessere AI-Resultate. Short ist live."
    KPI_24H="Durchschnittliche Wiedergabe >= 80%, 10 Saves/Shares"
    KPI_7D="2 qualifizierte Inbound-Anfragen"
    ;;
  "x"|"twitter")
    CHANNEL_BLOCK="$(cat <<EOF
## Channel Blueprint (X)
1. Hook-Tweet mit klarer Gegenthese
2. 4 Value-Tweets mit Beispielen
3. 1 CTA-Tweet mit "$CTA_KEYWORD"
4. 5 gezielte Antworten auf grosse Accounts in der Nische
EOF
)"
    PRIMARY_TITLE="Thread: Warum AI ohne Denkmodell dich langsamer macht"
    CREATIVE_CUE="Hook: Mehr Tools, weniger Ergebnis"
    DISTRIBUTION_TEASER="Heute ein Thread + Replies auf Top-Accounts."
    KPI_24H="Mind. 20 qualifizierte Replies, 3 DM-Starts"
    KPI_7D="1 Discovery-Call aus X"
    ;;
  "strategy"|"planning")
    CHANNEL_BLOCK="$(cat <<EOF
## Channel Blueprint (Strategy Day)
1. Wochenzahlen auswerten (CTR, retention, Leads)
2. Gewinner-Hooks clustern und 3 Wiederholungsformate definieren
3. Naechste 6 Assets sequenziell einplanen
4. CTA und Offer fuer die Woche fixieren
EOF
)"
    PRIMARY_TITLE="Wochensystem: Welche 3 Content-Formate bringen Leads"
    CREATIVE_CUE="Fokus: Wiederholung von Gewinner-Formaten"
    DISTRIBUTION_TEASER="Heute kein neues Format. Nur Skalierung der Gewinner."
    KPI_24H="1 belastbarer Wochenplan mit Prioritaeten"
    KPI_7D="Konstante Publikation ohne Lastspitzen"
    ;;
  *)
    CHANNEL_BLOCK="$(cat <<EOF
## Channel Blueprint ($CHANNEL)
1. Hook klar formulieren
2. Kernidee in 3 Punkten
3. CTA mit "$CTA_KEYWORD"
4. Ein Repurpose fuer zweiten Kanal
EOF
)"
    PRIMARY_TITLE="Philosophie x AI: Klarheit als Umsatzhebel"
    CREATIVE_CUE="Fokus: eine These, ein Beweis, ein CTA"
    DISTRIBUTION_TEASER="Heute fokussierter Asset-Run auf $CHANNEL."
    KPI_24H="1 publizierter Kernasset + 1 Repurpose"
    KPI_7D="Messbarer Inbound aus Content"
    ;;
esac

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

$SEQUENCE_PLAN

$CHANNEL_BLOCK

## Ready-to-use Assets
- Primary title: $PRIMARY_TITLE
- Creative cue: $CREATIVE_CUE
- Distribution teaser: $DISTRIBUTION_TEASER

## KPI Targets
- 24h: $KPI_24H
- 7d: $KPI_7D

## End-of-day Review
1. Welche Hook hatte die beste Retention?
2. Wo gab es den staerksten Drop-off?
3. Welches Format wird morgen 1:1 wiederholt?
EOF

cp "$OUT_FILE" "$OUT_LINK"
printf 'Daily sprint written: %s\n' "$OUT_FILE"
