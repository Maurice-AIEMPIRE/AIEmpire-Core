import os, re, json, subprocess, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HOME = str(Path.home())

# Suchmuster (ohne Secrets auszulesen)
PATTERNS = [
    r"TELEGRAM(_BOT)?_TOKEN",
    r"bot[_-]?token",
    r"telegram",
    r"t\.me",
    r"node\s",
    r"pm2",
    r"uvicorn",
    r"gunicorn",
    r"fastapi",
    r"flask",
    r"discord",
    r"openai",
    r"anthropic",
    r"kimi",
    r"agent",
    r"moltbook",
    r"openclaw",
    r"docker",
]

# Ordner, die oft relevant sind
ROOTS = [
    f"{HOME}/Projects",
    f"{HOME}/Code",
    f"{HOME}/Documents",
    f"{HOME}/Desktop",
    f"{HOME}/Downloads",
    f"{HOME}",
]

# Manche Ordner sind riesig/irrelevant -> skip
SKIP_DIRS = set([
    f"{HOME}/Library/Caches",
    f"{HOME}/Library/Containers",
    f"{HOME}/Library/Application Support/Google",
    f"{HOME}/Library/Application Support/Chrome",
    f"{HOME}/Library/Application Support/Firefox",
    f"{HOME}/Library/Mobile Documents",  # iCloud Drive kann groß sein
    f"{HOME}/.Trash",
    f"{HOME}/.npm",
    f"{HOME}/.cache",
])

TEXT_EXT = {".py",".js",".ts",".json",".yaml",".yml",".toml",".md",".env",".txt",".sh",".zsh",".conf",".ini"}


def run(cmd):
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        return out.strip()
    except Exception as e:
        return f"ERROR: {e}"


def list_running():
    return run(["bash","-lc", "ps aux | egrep -i 'telegram|bot|agent|python|node|pm2|uvicorn|gunicorn' | head -n 80 || true"])


def pm2_list():
    return run(["bash","-lc", "command -v pm2 >/dev/null 2>&1 && pm2 list || echo 'pm2 nicht gefunden'"])


def docker_ver():
    return run(["bash","-lc", "docker --version 2>/dev/null || echo 'docker nicht installiert'"])


def launch_agents():
    # LaunchAgents/Daemons: häufige Autostarts
    return {
        "user_launchagents": run(["bash","-lc", "ls -la ~/Library/LaunchAgents 2>/dev/null | head -n 120 || true"]),
        "system_launchdaemons": run(["bash","-lc", "ls -la /Library/LaunchDaemons 2>/dev/null | head -n 120 || true"]),
        "launchctl_list": run(["bash","-lc", "launchctl list | egrep -i 'telegram|bot|agent|python|node|pm2' | head -n 120 || true"])
    }


def cron_jobs():
    return run(["bash","-lc", "crontab -l 2>/dev/null | sed -n '1,200p' || echo 'keine crontab'"])


def scan_file(path):
    # liest nur Textdateien / kleine Dateien
    try:
        if path.suffix.lower() not in TEXT_EXT and path.name not in [".env", "Dockerfile", "docker-compose.yml", "docker-compose.yaml"]:
            return None
        if path.stat().st_size > 2_000_000:  # 2MB limit
            return None
        txt = path.read_text(errors="ignore")
        hits = []
        for pat in PATTERNS:
            if re.search(pat, txt, re.IGNORECASE):
                hits.append(pat)
        if hits:
            return {"file": str(path), "hits": sorted(set(hits))}
        return None
    except Exception:
        return None


def walk_collect_files(root):
    files = []
    rootp = Path(root)
    if not rootp.exists():
        return files
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        # skip dirs
        if any(str(Path(dirpath)).startswith(s) for s in SKIP_DIRS):
            dirnames[:] = []
            continue
        # prune hidden mega dirs
        dirnames[:] = [d for d in dirnames if d not in ["node_modules",".venv","venv","__pycache__",".git"]]
        for fn in filenames:
            p = Path(dirpath) / fn
            # quick include by name
            if fn in ["Dockerfile","docker-compose.yml","docker-compose.yaml",".env","package.json","requirements.txt","pyproject.toml","Procfile"]:
                files.append(p)
            else:
                # include only likely text
                if p.suffix.lower() in TEXT_EXT:
                    files.append(p)
    return files


def main():
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "running_processes": list_running(),
        "pm2": pm2_list(),
        "docker": docker_ver(),
        "launch": launch_agents(),
        "cron": cron_jobs(),
        "scan_summary": {},
        "findings": []
    }

    # "Kimi-Armee" Worker: parallel file scan
    all_files = []
    for r in ROOTS:
        all_files.extend(walk_collect_files(r))
    all_files = list(dict.fromkeys(all_files))  # unique

    report["scan_summary"]["roots"] = ROOTS
    report["scan_summary"]["files_considered"] = len(all_files)

    findings = []
    with ThreadPoolExecutor(max_workers=24) as ex:
        futs = [ex.submit(scan_file, p) for p in all_files]
        for f in as_completed(futs):
            res = f.result()
            if res:
                findings.append(res)

    # Sort by "interestingness"
    def score(item):
        f = item["file"].lower()
        s = 0
        if "telegram" in json.dumps(item["hits"]).lower(): s += 5
        if ".env" in f: s += 4
        if "docker" in f: s += 3
        if "package.json" in f: s += 3
        if "requirements" in f or "pyproject" in f: s += 2
        if "agent" in f: s += 2
        return (-s, f)

    findings.sort(key=score)
    report["findings"] = findings[:200]  # cap
    report["scan_summary"]["findings_count"] = len(findings)

    outpath = Path("KIMI_ARMY_AUDIT_REPORT.json")
    outpath.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"OK: Report geschrieben: {outpath.resolve()}  | findings_total={len(findings)}")

if __name__ == "__main__":
    main()
