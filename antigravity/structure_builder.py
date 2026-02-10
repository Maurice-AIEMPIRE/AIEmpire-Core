#!/usr/bin/env python3
"""
Structure Builder – Generates STRUCTURE_MAP.json + STRUCTURE_MAP.html dashboard
Usage: python3 antigravity/structure_builder.py && open antigravity/STRUCTURE_MAP.html
"""
import json
import os
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from antigravity.config import PROJECT_ROOT, STRUCTURE_MAP_JSON, STRUCTURE_MAP_HTML, ISSUES_FILE

def get_python_files():
    files = []
    for f in Path(PROJECT_ROOT).rglob("*.py"):
        if ".venv" in str(f) or "__pycache__" in str(f) or ".ruff_cache" in str(f):
            continue
        rel = str(f.relative_to(PROJECT_ROOT))
        try:
            lines = len(f.read_text(encoding="utf-8", errors="replace").split("\n"))
        except (OSError, UnicodeDecodeError):
            lines = 0
        files.append({"path": rel, "lines": lines, "dir": str(f.parent.relative_to(PROJECT_ROOT))})
    return sorted(files, key=lambda x: x["path"])

def get_imports(filepath):
    imports = []
    try:
        for line in Path(PROJECT_ROOT, filepath).read_text().split("\n"):
            line = line.strip()
            if line.startswith("import ") or line.startswith("from "):
                imports.append(line[:100])
    except (OSError, UnicodeDecodeError):
        pass
    return imports

def load_issues():
    if os.path.exists(ISSUES_FILE):
        return json.loads(Path(ISSUES_FILE).read_text())
    return {"total_issues": 0, "tasks": []}

def build_structure_map():
    files = get_python_files()
    issues = load_issues()
    # Build directory tree
    dirs = {}
    for f in files:
        d = f["dir"] if f["dir"] != "." else "root"
        dirs.setdefault(d, {"files": 0, "lines": 0})
        dirs[d]["files"] += 1
        dirs[d]["lines"] += f["lines"]
    # Hotspots (files with most issues)
    issue_files = {}
    for task in issues.get("tasks", []):
        for af in task.get("files_affected", []):
            issue_files[af] = issue_files.get(af, 0) + task.get("issue_count", 0)
    hotspots = sorted(issue_files.items(), key=lambda x: -x[1])[:20]

    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_files": len(files),
        "total_lines": sum(f["lines"] for f in files),
        "directories": dirs,
        "files": files,
        "hotspots": [{"file": h[0], "issue_count": h[1]} for h in hotspots],
        "issues_summary": {"total": issues.get("total_issues", 0),
            "tasks": len(issues.get("tasks", []))},
    }

def generate_html(data):
    tasks_json = "[]"
    if os.path.exists(ISSUES_FILE):
        tasks_json = json.dumps(json.loads(Path(ISSUES_FILE).read_text()).get("tasks",[]))
    hotspots_json = json.dumps(data["hotspots"])
    dirs_json = json.dumps(data["directories"])
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Antigravity Structure Dashboard</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',system-ui,sans-serif;background:#0a0a1a;color:#e0e0ff;min-height:100vh}}
.header{{background:linear-gradient(135deg,#1a0033,#0d001a);padding:2rem;border-bottom:1px solid #333}}
.header h1{{font-size:2rem;background:linear-gradient(90deg,#a855f7,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.header .stats{{display:flex;gap:2rem;margin-top:1rem}}
.stat{{background:rgba(168,85,247,0.1);border:1px solid rgba(168,85,247,0.3);border-radius:12px;padding:1rem 1.5rem}}
.stat .val{{font-size:1.8rem;font-weight:700;color:#a855f7}}
.stat .lbl{{font-size:0.8rem;color:#888;text-transform:uppercase}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;padding:2rem}}
.card{{background:rgba(255,255,255,0.03);border:1px solid #222;border-radius:16px;padding:1.5rem}}
.card h2{{font-size:1.2rem;color:#06b6d4;margin-bottom:1rem}}
.kanban{{display:flex;gap:1rem}}
.kanban-col{{flex:1;background:rgba(0,0,0,0.3);border-radius:12px;padding:1rem;min-height:200px}}
.kanban-col h3{{font-size:0.9rem;color:#666;margin-bottom:0.5rem;text-transform:uppercase}}
.task-card{{background:rgba(168,85,247,0.1);border:1px solid rgba(168,85,247,0.2);border-radius:8px;padding:0.8rem;margin-bottom:0.5rem;font-size:0.85rem}}
.task-card .tid{{color:#a855f7;font-weight:600}}
.task-card .owner{{color:#06b6d4;font-size:0.75rem}}
.hotspot{{display:flex;justify-content:space-between;padding:0.5rem 0;border-bottom:1px solid #1a1a2e;font-size:0.85rem}}
.hotspot .count{{color:#f43f5e;font-weight:600}}
.dir-bar{{display:flex;align-items:center;gap:0.5rem;margin-bottom:0.4rem;font-size:0.8rem}}
.dir-bar .bar{{height:8px;background:linear-gradient(90deg,#a855f7,#06b6d4);border-radius:4px}}
.dir-bar .name{{min-width:120px;color:#888}}
@media(max-width:768px){{.grid{{grid-template-columns:1fr}}.header .stats{{flex-wrap:wrap}}}}
</style></head><body>
<div class="header">
<h1>⚡ Antigravity Structure Dashboard</h1>
<p style="color:#666;margin:0.5rem 0">Godmode Programmer – {data['generated_at']}</p>
<div class="stats">
<div class="stat"><div class="val">{data['total_files']}</div><div class="lbl">Python Files</div></div>
<div class="stat"><div class="val">{data['total_lines']:,}</div><div class="lbl">Lines of Code</div></div>
<div class="stat"><div class="val">{data['issues_summary']['total']}</div><div class="lbl">Issues</div></div>
<div class="stat"><div class="val">{data['issues_summary']['tasks']}</div><div class="lbl">Tasks</div></div>
</div></div>
<div class="grid">
<div class="card"><h2>📋 Kanban Board</h2><div class="kanban" id="kanban"></div></div>
<div class="card"><h2>🔥 Hotspots</h2><div id="hotspots"></div></div>
<div class="card" style="grid-column:span 2"><h2>📁 Directory Map</h2><div id="dirs"></div></div>
</div>
<script>
const tasks={tasks_json};
const hotspots={hotspots_json};
const dirs={dirs_json};
// Kanban
const kb=document.getElementById('kanban');
const cols={{'backlog':[],'in_progress':[],'done':[]}};
tasks.forEach(t=>{{const s=t.status||'backlog';(cols[s]||cols.backlog).push(t)}});
Object.entries(cols).forEach(([name,items])=>{{
  const col=document.createElement('div');col.className='kanban-col';
  col.innerHTML='<h3>'+name.replace('_',' ')+'</h3>';
  items.forEach(t=>{{const c=document.createElement('div');c.className='task-card';
    c.innerHTML='<div class="tid">'+t.id+'</div>'+t.label+'<div class="owner">→ '+t.owner_agent.toUpperCase()+' | '+t.issue_count+' issues</div>';
    col.appendChild(c)}});
  kb.appendChild(col)}});
// Hotspots
const hs=document.getElementById('hotspots');
hotspots.forEach(h=>{{const d=document.createElement('div');d.className='hotspot';
  d.innerHTML='<span>'+h.file+'</span><span class="count">'+h.issue_count+' issues</span>';hs.appendChild(d)}});
// Dirs
const ds=document.getElementById('dirs');
const maxLines=Math.max(...Object.values(dirs).map(d=>d.lines),1);
Object.entries(dirs).sort((a,b)=>b[1].lines-a[1].lines).forEach(([name,d])=>{{
  const el=document.createElement('div');el.className='dir-bar';
  const pct=Math.max((d.lines/maxLines)*100,2);
  el.innerHTML='<span class="name">'+name+'</span><div class="bar" style="width:'+pct+'%"></div><span>'+d.files+' files, '+d.lines+' lines</span>';
  ds.appendChild(el)}});
</script></body></html>"""

def main():
    from rich.console import Console
    c = Console()
    c.print("[bold cyan]🏗️ Building Structure Map...[/bold cyan]")
    data = build_structure_map()
    Path(STRUCTURE_MAP_JSON).write_text(json.dumps(data, indent=2))
    c.print(f"[green]✓[/green] {STRUCTURE_MAP_JSON}")
    Path(STRUCTURE_MAP_HTML).write_text(generate_html(data))
    c.print(f"[green]✓[/green] {STRUCTURE_MAP_HTML}")
    c.print(f"\n[bold]open {STRUCTURE_MAP_HTML}[/bold]")

if __name__ == "__main__":
    main()
