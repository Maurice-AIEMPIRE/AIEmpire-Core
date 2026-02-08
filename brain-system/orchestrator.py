#!/usr/bin/env python3
"""
BRAIN SYSTEM ORCHESTRATOR
=========================
Steuert alle 7+1 Gehirne wie ein echtes Nervensystem.
Jedes Gehirn ist ein spezialisierter Agent mit eigenem Prompt.
Kommunikation ueber "Synapsen" (Event Queue).

FREE Stack: Ollama + Kimi K2.5 + OpenClaw + Antigravity
Claude nur als externer Berater (kein Token-Dependency!)
"""

import asyncio
import json
import os
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# ============================================
# BRAIN DEFINITIONS
# ============================================

BRAINS = {
    "brainstem": {
        "name": "The Guard",
        "model": "bash",  # Kein LLM — deterministisch
        "schedule": ["06:00", "hourly"],
        "priority": 0,  # Hoechste Prioritaet
    },
    "neocortex": {
        "name": "The Visionary",
        "model": "kimi-k2.5",  # Braucht grosses Context Window
        "schedule": ["08:00", "sunday-10:00"],
        "priority": 1,
    },
    "prefrontal": {
        "name": "The CEO",
        "model": "kimi-k2.5",  # Bestes Reasoning (Kimi statt Claude!)
        "schedule": ["09:00", "18:00"],
        "priority": 1,
    },
    "temporal": {
        "name": "The Mouth",
        "model": "kimi-k2.5",  # Content-Generierung
        "schedule": ["10:00-16:00"],
        "priority": 2,
    },
    "parietal": {
        "name": "The Numbers",
        "model": "ollama:qwen2.5-coder:7b",  # Lokal, FREE
        "schedule": ["17:00", "sunday-report"],
        "priority": 2,
    },
    "limbic": {
        "name": "The Drive",
        "model": "ollama:qwen2.5-coder:7b",  # Schnell, lokal
        "schedule": ["07:00", "19:00"],
        "priority": 3,
    },
    "cerebellum": {
        "name": "The Hands",
        "model": "ollama:qwen2.5-coder:7b",  # Code lokal
        "schedule": ["10:00-16:00", "night"],
        "priority": 2,
    },
    "hippocampus": {
        "name": "The Memory",
        "model": "sqlite+redplanet",  # Persistent, kein LLM
        "schedule": ["continuous", "22:00-consolidation"],
        "priority": 1,
    },
}

# ============================================
# SYNAPSE (Inter-Brain Communication)
# ============================================

DB_PATH = os.path.expanduser("~/.openclaw/brain-system/synapses.db")


def init_synapse_db():
    """Initialize synapse database for inter-brain communication"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS synapses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        from_brain TEXT,
        to_brain TEXT,
        message_type TEXT,
        payload TEXT,
        priority INTEGER DEFAULT 5,
        processed INTEGER DEFAULT 0,
        processed_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        name TEXT UNIQUE,
        description TEXT,
        xp_reward INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS xp_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        action TEXT,
        xp_earned INTEGER,
        total_xp INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS streaks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        current_count INTEGER DEFAULT 0,
        longest_count INTEGER DEFAULT 0,
        last_updated TEXT
    )''')
    conn.commit()
    return conn


def send_synapse(from_brain, to_brain, msg_type, payload, priority=5):
    """Send a message between brains"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO synapses
        (timestamp, from_brain, to_brain, message_type, payload, priority)
        VALUES (?, ?, ?, ?, ?, ?)''',
        (datetime.utcnow().isoformat(), from_brain, to_brain,
         msg_type, json.dumps(payload), priority))
    conn.commit()
    conn.close()


def receive_synapses(brain_name, limit=10):
    """Receive pending messages for a brain"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT id, from_brain, message_type, payload, priority
        FROM synapses WHERE to_brain = ? AND processed = 0
        ORDER BY priority ASC, timestamp ASC LIMIT ?''',
        (brain_name, limit))
    messages = c.fetchall()

    # Mark as processed
    for msg in messages:
        c.execute('UPDATE synapses SET processed = 1, processed_at = ? WHERE id = ?',
                  (datetime.utcnow().isoformat(), msg[0]))
    conn.commit()
    conn.close()

    return [{"id": m[0], "from": m[1], "type": m[2],
             "payload": json.loads(m[3]), "priority": m[4]} for m in messages]


# ============================================
# BRAIN RUNNERS
# ============================================

def run_brainstem():
    """BRAINSTEM: Health checks (no LLM needed)"""
    results = {}

    # Ollama check
    try:
        r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                           "http://localhost:11434/api/tags"],
                          capture_output=True, text=True, timeout=5)
        results["ollama"] = "OK" if r.stdout.strip() == "200" else "DOWN"
    except:
        results["ollama"] = "DOWN"

    # Disk space
    try:
        r = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
        lines = r.stdout.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            results["disk_free"] = parts[3] if len(parts) > 3 else "unknown"
    except:
        results["disk_free"] = "unknown"

    # OpenClaw
    try:
        r = subprocess.run(["openclaw", "health"], capture_output=True, text=True, timeout=10)
        results["openclaw"] = "OK" if r.returncode == 0 else "WARN"
    except:
        results["openclaw"] = "NOT_RUNNING"

    # Report
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    report = f"## HEALTH REPORT {timestamp}\n\n"
    report += "| System | Status |\n|--------|--------|\n"
    for system, status in results.items():
        emoji = "✅" if status in ["OK", "healthy"] else "⚠️" if status == "WARN" else "❌"
        report += f"| {system} | {emoji} {status} |\n"

    # Alert if critical
    if any(v in ["DOWN", "CRITICAL"] for v in results.values()):
        send_synapse("brainstem", "prefrontal", "ALERT",
                    {"severity": "HIGH", "systems": results}, priority=0)

    return report


def run_limbic_morning():
    """LIMBIC: Morning briefing"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Get XP
    c.execute('SELECT total_xp FROM xp_log ORDER BY id DESC LIMIT 1')
    xp_row = c.fetchone()
    total_xp = xp_row[0] if xp_row else 0
    level = total_xp // 100 + 1

    # Get streaks
    c.execute('SELECT name, current_count FROM streaks')
    streaks = {row[0]: row[1] for row in c.fetchall()}
    conn.close()

    # Build briefing
    today = datetime.now().strftime("%Y-%m-%d")
    briefing = f"## MORNING BRIEFING {today}\n\n"
    briefing += f"Level: {level} | XP: {total_xp} | "

    if streaks:
        streak_str = " | ".join([f"{k}: {v} Tage 🔥" for k, v in streaks.items()])
        briefing += streak_str
    briefing += "\n\n"

    # Motivation based on level
    if level < 5:
        briefing += "💪 Du bist am Anfang — jeder erste Schritt zaehlt!\n"
    elif level < 20:
        briefing += "🚀 Momentum baut sich auf — nicht stoppen!\n"
    elif level < 50:
        briefing += "⚡ Du bist im Flow — das Empire waechst!\n"
    else:
        briefing += "👑 UNSTOPPABLE. Das Empire ist Realitaet.\n"

    return briefing


def add_xp(action, xp_amount):
    """Add XP to the system"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT total_xp FROM xp_log ORDER BY id DESC LIMIT 1')
    row = c.fetchone()
    current = row[0] if row else 0
    new_total = current + xp_amount

    c.execute('INSERT INTO xp_log (timestamp, action, xp_earned, total_xp) VALUES (?, ?, ?, ?)',
              (datetime.utcnow().isoformat(), action, xp_amount, new_total))
    conn.commit()
    conn.close()

    # Check level up
    old_level = current // 100 + 1
    new_level = new_total // 100 + 1
    if new_level > old_level:
        send_synapse("limbic", "prefrontal", "LEVEL_UP",
                    {"old_level": old_level, "new_level": new_level}, priority=2)

    return new_total


def update_streak(streak_name):
    """Update a streak counter"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('SELECT current_count, longest_count, last_updated FROM streaks WHERE name = ?',
              (streak_name,))
    row = c.fetchone()

    today = datetime.now().strftime("%Y-%m-%d")

    if row:
        current, longest, last = row
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        if last == yesterday or last == today:
            new_count = current + 1 if last == yesterday else current
        else:
            new_count = 1  # Streak broken
        new_longest = max(longest, new_count)
        c.execute('UPDATE streaks SET current_count = ?, longest_count = ?, last_updated = ? WHERE name = ?',
                  (new_count, new_longest, today, streak_name))
    else:
        c.execute('INSERT INTO streaks (name, current_count, longest_count, last_updated) VALUES (?, 1, 1, ?)',
                  (streak_name, today))

    conn.commit()
    conn.close()


# ============================================
# MAIN ORCHESTRATOR
# ============================================

def run_daily_cycle():
    """Run the complete daily brain cycle"""
    init_synapse_db()
    reports = {}

    print("=" * 60)
    print(f"BRAIN SYSTEM — Daily Cycle {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Phase 1: BRAINSTEM (06:00)
    print("\n🧠 BRAINSTEM — Health Check...")
    reports["brainstem"] = run_brainstem()
    print(reports["brainstem"])

    # Phase 2: LIMBIC (07:00)
    print("\n🔥 LIMBIC — Morning Briefing...")
    reports["limbic"] = run_limbic_morning()
    print(reports["limbic"])

    # Phase 3: Signal to other brains
    send_synapse("orchestrator", "neocortex", "START_DAY", {"date": datetime.now().isoformat()})
    send_synapse("orchestrator", "prefrontal", "START_DAY", {"date": datetime.now().isoformat()})
    send_synapse("orchestrator", "temporal", "START_CONTENT", {"quota": 5})
    send_synapse("orchestrator", "parietal", "PREPARE_KPI", {})
    send_synapse("orchestrator", "cerebellum", "CHECK_AUTOMATIONS", {})

    print("\n✅ All brains signaled. Daily cycle initialized.")
    print(f"Active brains: {len(BRAINS)}")
    print(f"Pending synapses: Check with --status")

    return reports


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Brain System Orchestrator')
    parser.add_argument('--cycle', action='store_true', help='Run daily cycle')
    parser.add_argument('--health', action='store_true', help='Run brainstem health check')
    parser.add_argument('--morning', action='store_true', help='Run morning briefing')
    parser.add_argument('--xp', type=int, help='Add XP (e.g. --xp 50 --action "Posted content")')
    parser.add_argument('--action', type=str, default='manual', help='XP action description')
    parser.add_argument('--streak', type=str, help='Update streak (e.g. --streak content)')
    parser.add_argument('--status', action='store_true', help='Show brain status')

    args = parser.parse_args()
    init_synapse_db()

    if args.cycle:
        run_daily_cycle()
    elif args.health:
        print(run_brainstem())
    elif args.morning:
        print(run_limbic_morning())
    elif args.xp:
        total = add_xp(args.action, args.xp)
        print(f"XP added: +{args.xp} | Total: {total} | Level: {total // 100 + 1}")
    elif args.streak:
        update_streak(args.streak)
        print(f"Streak '{args.streak}' updated!")
    elif args.status:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM synapses WHERE processed = 0')
        pending = c.fetchone()[0]
        c.execute('SELECT from_brain, COUNT(*) FROM synapses GROUP BY from_brain')
        brain_msgs = c.fetchall()
        print(f"Pending synapses: {pending}")
        print(f"Messages by brain:")
        for brain, count in brain_msgs:
            print(f"  {brain}: {count}")
        conn.close()
    else:
        parser.print_help()
