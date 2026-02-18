# MONSTER_CONSTRUCT_RUNBOOK_2026-02-18

## Ziel
- Ein einziger Befehl baut den kompletten Betriebsstatus neu auf.
- Ergebnis ist ein Master-Artefakt mit Runtime-, Revenue- und Gap-Status.

## Hauptbefehl
```bash
automation/scripts/run_monster_construct.sh
```

## Aggressive Konsolidierung
```bash
automation/scripts/run_monster_construct.sh --apply-consolidation
```

## Was der Runner ausfuehrt
1. `preflight_gate.py`
2. `audit_infra_runtime.py --mode snapshot`
3. `audit_infra_runtime.py --mode verify`
4. `consolidate_launchd_runtime.py` (dry-run oder apply)
5. `write_daily_kpi.py`
6. `build_master_chat_artifact_index.py`
7. `build_monster_construct.py`

## Outputs
- `/Users/maurice/Documents/New project/00_SYSTEM/infra/SYSTEM_INVENTORY_YYYY-MM-DD.json`
- `/Users/maurice/Documents/New project/00_SYSTEM/infra/LAUNCHD_CONSOLIDATION_REPORT_YYYY-MM-DD.md`
- `/Users/maurice/Documents/New project/00_SYSTEM/MONSTER_CONSTRUCT_MASTER.md`
- `/Users/maurice/Documents/New project/00_SYSTEM/MONSTER_CONSTRUCT_MASTER.json`
- `/Users/maurice/Documents/New project/automation/runs/monster_construct/monster_construct_*.log`

## Betriebsrhythmus (08:00-23:00)
- 07:55: Preflight
- 08:00: Service-Outbound + selektive Automations
- 12:30: KPI-Checkpoint
- 18:00: Follow-ups + Offers
- 22:30: Degrade/Snapshot

## Verifikation
- `python3 automation/scripts/audit_infra_runtime.py --mode verify --output 00_SYSTEM/infra/SYSTEM_INVENTORY_$(date +%Y-%m-%d).json`
- `python3 automation/scripts/preflight_gate.py`
- `cat 00_SYSTEM/MONSTER_CONSTRUCT_MASTER.md`
