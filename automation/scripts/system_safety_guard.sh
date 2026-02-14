#!/usr/bin/env bash
set -euo pipefail

# Returns 0 if the system is safe for heavy workloads.
# Returns non-zero if CPU load/thermal/memory pressure exceeds thresholds.

MAX_LOAD_PER_CORE="${MAX_LOAD_PER_CORE:-0.85}"       # 0.85 means 85% per core average on 1m window
MIN_CPU_SPEED_LIMIT="${MIN_CPU_SPEED_LIMIT:-80}"     # pmset CPU speed limit below this => thermal throttling
MIN_MEMORY_FREE_PERCENT="${MIN_MEMORY_FREE_PERCENT:-12}"  # free memory below this => skip heavy tasks

LOAD1="$(uptime | awk -F'load averages?: ' '{print $2}' | awk '{print $1}' | tr -d ',')"
CORES="$(sysctl -n hw.ncpu 2>/dev/null || echo 4)"
if [ -z "$LOAD1" ]; then
  LOAD1="0"
fi
if [ -z "$CORES" ] || ! [[ "$CORES" =~ ^[0-9]+$ ]] || [ "$CORES" -le 0 ]; then
  CORES=4
fi

LOAD_PER_CORE="$(python3 - <<'PY' "$LOAD1" "$CORES"
import sys
load = float(sys.argv[1])
cores = max(1, int(sys.argv[2]))
print(f"{load/cores:.3f}")
PY
)"

CPU_SPEED_LIMIT="$(pmset -g therm 2>/dev/null | awk '/CPU_Speed_Limit/{print $3}' | head -n1 || true)"
if [ -z "${CPU_SPEED_LIMIT:-}" ]; then
  CPU_SPEED_LIMIT=100
fi

MEMORY_FREE_PERCENT="$(memory_pressure -Q 2>/dev/null | awk -F': ' '/System-wide memory free percentage/{gsub("%","",$2); print $2}' | head -n1 || true)"
if [ -z "${MEMORY_FREE_PERCENT:-}" ]; then
  MEMORY_FREE_PERCENT=100
fi

echo "[safety] load1=$LOAD1 cores=$CORES load_per_core=$LOAD_PER_CORE cpu_speed_limit=$CPU_SPEED_LIMIT memory_free_percent=$MEMORY_FREE_PERCENT"

python3 - <<'PY' "$LOAD_PER_CORE" "$MAX_LOAD_PER_CORE" "$CPU_SPEED_LIMIT" "$MIN_CPU_SPEED_LIMIT" "$MEMORY_FREE_PERCENT" "$MIN_MEMORY_FREE_PERCENT"
import sys

load_per_core = float(sys.argv[1])
max_load_per_core = float(sys.argv[2])
cpu_speed_limit = float(sys.argv[3])
min_cpu_speed_limit = float(sys.argv[4])
memory_free_percent = float(sys.argv[5])
min_memory_free_percent = float(sys.argv[6])

if load_per_core > max_load_per_core:
    print(f"[safety] blocked: load_per_core {load_per_core:.3f} > {max_load_per_core:.3f}")
    raise SystemExit(2)
if cpu_speed_limit < min_cpu_speed_limit:
    print(f"[safety] blocked: cpu_speed_limit {cpu_speed_limit:.0f} < {min_cpu_speed_limit:.0f}")
    raise SystemExit(3)
if memory_free_percent < min_memory_free_percent:
    print(f"[safety] blocked: memory_free_percent {memory_free_percent:.1f} < {min_memory_free_percent:.1f}")
    raise SystemExit(4)

print("[safety] ok")
PY
