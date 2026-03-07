# 📊 ANTIGRAVITY DASHBOARD – Aktuelle Strukturen

> Dieses Dokument beschreibt, wie du den Antigravity Dashboard immer aktuell hältst.

---

## Dashboard bauen

```bash
python3 antigravity/structure_builder.py && open antigravity/STRUCTURE_MAP.html
```

Das generiert:

- `STRUCTURE_MAP.json` – Maschinenlesbarer Repo-Überblick
- `STRUCTURE_MAP.html` – Visuelles Dashboard mit:
  - **Kanban Board** (Backlog / In Progress / Done)
  - **Hotspots** (Dateien mit meisten Issues)
  - **Directory Map** (Größe und Verteilung des Codes)

---

## Automatisch aktuell halten

### Nach jedem Swarm-Run

```bash
python3 empire_launch.py --full-pipeline
```

Das macht automatisch: collect → cluster → swarm → dashboard.

### Nur Dashboard updaten

```bash
python3 antigravity/structure_builder.py
```

### Nur Issues updaten

```bash
python3 antigravity/collect_reports.py && python3 antigravity/cluster_issues.py
```

---

## Dateien-Übersicht

| Datei | Zweck |
|---|---|
| `antigravity/STRUCTURE_MAP.html` | Browser-Dashboard |
| `antigravity/STRUCTURE_MAP.json` | Maschinenlesbare Struktur |
| `antigravity/ISSUES.json` | Alle Issues als Tasks |
| `antigravity/ISSUES_KANBAN.md` | Kanban als Markdown |
| `antigravity/_reports/full_report.json` | Rohe Fehlerdaten |
| `antigravity/_reports/swarm_*.json` | Swarm-Run Results |

---

## Workflow: Tägliche Routine

```
1. python3 empire_launch.py --status          # Was läuft?
2. python3 antigravity/collect_reports.py      # Fehler sammeln
3. python3 antigravity/cluster_issues.py       # Clustern
4. python3 antigravity/swarm_run.py --mode fix-first --task "Top 5 Issues fixen"
5. python3 empire_launch.py --smoke-test       # Alles ok?
6. python3 antigravity/structure_builder.py    # Dashboard updaten
7. open antigravity/STRUCTURE_MAP.html         # Überblick
```
