#!/bin/bash
# Memory Monitor - Run continuously

while true; do
    TOTAL=$(free -h | awk 'NR==2 {print $2}')
    USED=$(free -h | awk 'NR==2 {print $3}')
    FREE=$(free -h | awk 'NR==2 {print $4}')
    PERCENT=$(free | awk 'NR==2 {printf "%.0f", $3/$2*100}')

    TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

    if [ $PERCENT -gt 90 ]; then
        echo "[$TIMESTAMP] CRITICAL: $PERCENT% - $USED / $TOTAL (FREE: $FREE)"
        # Kill background jobs that aren't essential
        pkill -f "python.*test" 2>/dev/null
        pkill -f "node" 2>/dev/null
    elif [ $PERCENT -gt 75 ]; then
        echo "[$TIMESTAMP] WARNING: $PERCENT% - $USED / $TOTAL"
    else
        echo "[$TIMESTAMP] OK: $PERCENT% - $USED / $TOTAL"
    fi

    sleep 30
done
