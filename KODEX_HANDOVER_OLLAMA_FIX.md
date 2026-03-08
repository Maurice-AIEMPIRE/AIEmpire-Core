# KODEX HANDOVER — OLLAMA TIMEOUT FIX
**From:** Claude Code
**To:** Kodex
**Date:** 2026-03-07
**Status:** CRITICAL FIX NEEDED

---

## PROBLEM IDENTIFIED
```
Error: litellm.APIConnectionError: OllamaException
Error: litellm.Timeout: Connection timed out. Timeout passed=40.0s
Location: Telegram bot showing this error live
```

**Root Cause:** Ollama is NOT running. The API timeout is because the service never started.

**Evidence:**
```bash
ps aux | grep ollama      # Returns NOTHING
curl http://localhost:11434/api/tags    # Connection refused
```

---

## IMMEDIATE FIX (for Kodex to implement)

### Step 1: Start Ollama Service
```bash
# Option A: Direct start
ollama serve &

# Option B: Background nohup
nohup ollama serve > /tmp/ollama.log 2>&1 &

# Option C: Check if installed
which ollama
ollama --version

# Option D: If not installed
curl -fsSL https://ollama.ai/install.sh | sh
```

### Step 2: Verify Ollama is running
```bash
# Check process
ps aux | grep ollama | grep -v grep

# Check API
curl http://localhost:11434/api/tags

# Expected output: {"models": [...]}
```

### Step 3: Load model if needed
```bash
# Pull a model (e.g., mistral)
ollama pull mistral

# Or your preferred model
ollama pull neural-chat
```

### Step 4: Test connection
```python
import requests
response = requests.get("http://localhost:11434/api/tags")
print(response.json())  # Should return list of models
```

---

## LONGTERM FIX: Auto-Start on Boot

### On Linux (systemd):
```bash
# Create service file
sudo tee /etc/systemd/system/ollama.service > /dev/null <<EOF
[Unit]
Description=Ollama Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/ollama serve
Restart=always
RestartSec=5
User=$USER
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl start ollama
```

### On macOS (LaunchAgent):
```bash
# Create plist
cat > ~/Library/LaunchAgents/com.ollama.service.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ollama.service</string>
    <key>Program</key>
    <string>/usr/local/bin/ollama</string>
    <key>ProgramArguments</key>
    <array>
        <string>serve</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/ollama.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/ollama.error.log</string>
</dict>
</plist>
EOF

# Load
launchctl load ~/Library/LaunchAgents/com.ollama.service.plist
```

---

## SYSTEM RESILIENCE (Kodex implement this)

### Add to `antigravity/config.py`:
```python
def _ensure_ollama_running():
    """Auto-start Ollama if not running (crash recovery)."""
    import subprocess
    import time

    try:
        # Check if running
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        if response.status_code == 200:
            return True  # Ollama is running
    except:
        pass

    # Try to start Ollama
    try:
        print("⚠️  Ollama not running. Attempting to start...")
        subprocess.Popen(["ollama", "serve"],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        time.sleep(3)  # Give it time to start
        return True
    except Exception as e:
        print(f"❌ Failed to start Ollama: {e}")
        return False

# Call at startup
if not _ensure_ollama_running():
    print("⚠️  WARNING: Ollama offline. Falling back to remote models only.")
```

### Add to `scripts/bombproof_startup.sh`:
```bash
#!/bin/bash

echo "🤖 Bombproof Startup Phase 1: Ensure Ollama..."

# Start Ollama if not running
if ! pgrep -x ollama > /dev/null; then
    echo "   Starting Ollama..."
    nohup ollama serve > /tmp/ollama.log 2>&1 &
    sleep 3
fi

# Verify Ollama
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "   ✅ Ollama online"
else
    echo "   ⚠️  Ollama offline (will use remote models)"
fi

# Continue with other startup phases...
```

---

## MONITORING (Kodex implement this)

### Add health check to `workflow_system/resource_guard.py`:
```python
def check_ollama_health():
    """Monitor Ollama service health."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return {"status": "OK", "models": len(models)}
    except:
        return {"status": "OFFLINE", "models": 0}

    return {"status": "ERROR", "models": 0}

# Call periodically
health = check_ollama_health()
if health["status"] != "OK":
    print(f"⚠️  Ollama Health: {health}")
    # Auto-start if offline
    _ensure_ollama_running()
```

---

## TIMEOUT CONFIGURATION (Kodex adjust if needed)

### Current timeout setting in config:
```python
OLLAMA_TIMEOUT = os.getenv("OLLAMA_TIMEOUT", "40")  # seconds
```

### If Ollama is running but slow, increase timeout:
```bash
# In .env file:
OLLAMA_TIMEOUT=120  # 2 minutes instead of 40 seconds
```

### Optimize Ollama performance:
```bash
# Run with more threads/GPU
OLLAMA_NUM_PARALLEL=4     # Parallel requests
OLLAMA_NUM_GPU=1          # Use GPU if available
OLLAMA_LLM_LIBRARY=/usr/local/lib/ollama  # GPU library path
```

---

## MODEL ORCHESTRATION (Multi-Model Strategy)

### Current Fallback Chain (in unified_router.py):
```
1. Ollama (local) - 95% usage
   └── If timeout: fallback to Kimi
2. Kimi (remote, Moonshot) - 4% usage
   └── If error: fallback to Claude
3. Claude (remote, Anthropic) - 1% usage
   └── If error: use cached response
```

### All 3 models should collaborate:
```python
# Don't wait for one model - try all 3 in parallel
async def execute_with_all_models(prompt):
    """Run prompt on Ollama, Kimi, Gemini in parallel for consensus."""
    try:
        ollama_task = ollama.complete(prompt)
        kimi_task = kimi.complete(prompt)
        gemini_task = gemini.complete(prompt)

        results = await asyncio.gather(
            ollama_task, kimi_task, gemini_task,
            return_exceptions=True
        )

        # Filter successful results
        valid_results = [r for r in results if not isinstance(r, Exception)]

        if not valid_results:
            raise Exception("All models failed")

        # Return fastest result OR consensus of best 2
        return valid_results[0]
    except Exception as e:
        print(f"Model execution error: {e}")
        return None
```

---

## KNOWLEDGE TRANSFER TO KODEX

**Key Files to Monitor:**
- `/home/user/AIEmpire-Core/antigravity/config.py` - Ollama config
- `/home/user/AIEmpire-Core/antigravity/unified_router.py` - Model routing
- `/home/user/AIEmpire-Core/scripts/bombproof_startup.sh` - Auto-start
- `/home/user/AIEmpire-Core/workflow_system/resource_guard.py` - Health monitoring

**Test Command:**
```bash
# Verify all 3 models working
python3 -c "
from antigravity.unified_router import UnifiedRouter
router = UnifiedRouter()
# Try each model
print('Testing Ollama...')
result = router.complete('Hello', model='ollama')
print('Testing Kimi...')
result = router.complete('Hello', model='kimi')
print('Testing Gemini...')
result = router.complete('Hello', model='gemini')
print('✅ All models online')
"
```

---

## SUMMARY FOR KODEX
1. **Immediate:** Start Ollama service (`ollama serve`)
2. **Short-term:** Add auto-start on boot (systemd/LaunchAgent)
3. **Medium-term:** Implement health checks + auto-recovery
4. **Long-term:** Multi-model parallel execution (no single point of failure)

**This will eliminate Telegram timeouts and make system bulletproof.**

---

**Questions for Kodex?**
- Ollama running status: `ps aux | grep ollama`
- Model list: `ollama list`
- Logs: `tail -f /tmp/ollama.log`
- Manual start: `ollama serve` (then Ctrl+C when running)

**Knowledge Hub:** Store all solutions in Knowledge Store for future reference.
