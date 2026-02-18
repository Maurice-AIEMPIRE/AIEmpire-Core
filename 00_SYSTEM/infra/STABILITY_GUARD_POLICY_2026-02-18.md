# STABILITY_GUARD_POLICY_2026-02-18

## Objective
Ensure heavy automations never crash-loop the machine. Use degrade mode and deterministic backoff.

## Guard Rules
- Time window: heavy jobs only `08:00-23:00` local time.
- Preflight gate required before heavy runs.
- Block conditions:
  - `load_per_core > 0.85`
  - `memory_free_pct < 12`
  - required endpoints unavailable

## Retry / Backoff
- Attempt 1: wait 5 min
- Attempt 2: wait 15 min
- Attempt 3+: wait 30 min
- On repeated failure, switch to degrade maintenance only.

## Required Scripts
- `automation/scripts/preflight_gate.py`
- `automation/scripts/run_stability_quickfix.sh`

## Verification
- `python3 automation/scripts/preflight_gate.py`
- `automation/scripts/run_stability_quickfix.sh check`
