#!/usr/bin/env python3
"""
N8N BRIDGE AGENT
Connects the Local Empire Cluster to N8N Webhooks.
Monitors: LIVE_QUEUE.md, leads/ folder.
Pushes data to: http://localhost:5678/webhook/godmode
"""

import time
import json
import requests
import os
from pathlib import Path
import socket

# Config
N8N_WEBHOOK_URL = "http://localhost:5678/webhook/godmode"
QUEUE_FILE = Path(__file__).parent / "LIVE_QUEUE.md"
WATCH_DIR = Path(__file__).parent / "leads"
INTERVAL = 10

def check_n8n_health():
    """Checks if N8N is listening on port 5678."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 5678))
    sock.close()
    if result == 0:
        print("✅ N8N is ONLINE (Port 5678)")
        return True
    else:
        print("⚠️ WARNING: N8N is NOT reachable on Port 5678.")
        print("👉 Please start N8N via Desktop App or 'n8n start'.")
        return False

def push_to_n8n(payload):
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=5)
        if response.status_code == 200:
            print(f"✅ Pushed to N8N: {payload.get('type')}")
            return True
        else:
            print(f"⚠️ N8N Error: {response.status_code}")
    except Exception as e:
        # N8N might not be running, don't crash the bridge
        # print(f"❌ Connection Error: {e}") 
        pass
    return False

def run_bridge():
    print(f"🌉 N8N BRIDGE ACTIVE")
    print(f"🔗 TARGET: {N8N_WEBHOOK_URL}")
    
    check_n8n_health()
    
    print("="*60)

    # Track file sizes/mod times to detect changes
    last_queue_size = 0
    if QUEUE_FILE.exists():
        last_queue_size = QUEUE_FILE.stat().st_size

    processed_leads = set()
    # Initial scan of leads
    if LEADS_DIR.exists():
        for f in LEADS_DIR.glob("*.md"):
            processed_leads.add(str(f))

    while True:
        # 1. Monitor Queue (New Posts)
        if QUEUE_FILE.exists():
            current_size = QUEUE_FILE.stat().st_size
            if current_size > last_queue_size:
                # New content added
                with open(QUEUE_FILE, "r") as f:
                    f.seek(last_queue_size)
                    new_content = f.read()
                
                if new_content.strip():
                    push_to_n8n({
                        "type": "new_post",
                        "content": new_content,
                        "source": "attacke_autopilot",
                        "timestamp": time.time()
                    })
                
                last_queue_size = current_size

        # 2. Monitor Leads (New Files)
        if WATCH_DIR.exists():
            for f in WATCH_DIR.glob("*.md"):
                if str(f) not in processed_leads:
                    with open(f, "r") as lead_file:
                        content = lead_file.read()
                    
                    push_to_n8n({
                        "type": "new_lead_list",
                        "filename": f.name,
                        "content": content,
                        "timestamp": time.time()
                    })
                    
                    processed_leads.add(str(f))

        # 3. Simulate Sales (For Testing Notifications)
        # In a real scenario, this would be a webhook listener
        if time.time() % 60 < 5: # Roughly every minute for testing
            import random
            products = ["AI Setup", "Viral Velocity", "Automated Cashflow"]
            push_to_n8n({
                "type": "sale_alert",
                "product": random.choice(products),
                "amount": random.choice([47, 97, 997]),
                "email": "test.customer@gmail.com",
                "timestamp": time.time()
            })
            print("💰 SIMULATED SALE ALERT SENT!")

        time.sleep(INTERVAL)

if __name__ == "__main__":
    run_bridge()
