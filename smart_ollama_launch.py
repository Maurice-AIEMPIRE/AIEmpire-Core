#!/usr/bin/env python3

"""
smart_ollama_launch.py - RAM-aware Ollama launcher
Checks memory before starting models
"""

import subprocess
import sys
import time
import psutil

def get_memory_mb():
    """Get current memory usage in MB"""
    mem = psutil.virtual_memory()
    return mem.used // (1024 * 1024), mem.available // (1024 * 1024)

def check_ollama_running():
    """Check if Ollama is running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'ollama'],
                              capture_output=True, text=True)
        return len(result.stdout.strip().split('\n')) > 0
    except:
        return False

def main():
    print("🧠 Smart Ollama Launcher")
    print("========================")

    # Check memory
    used, available = get_memory_mb()
    total = used + available
    percent_used = (used / total) * 100

    print(f"Memory: {used}MB used, {available}MB free ({percent_used:.1f}%)")

    # Minimum requirements
    MIN_FREE_MB = 1024  # 1GB free
    MAX_USED_PERCENT = 70

    if available < MIN_FREE_MB or percent_used > MAX_USED_PERCENT:
        print(f"❌ Insufficient memory! Need >{MIN_FREE_MB}MB free and <{MAX_USED_PERCENT}% used")
        print("Run QUICK_MEMORY_FIX.sh first")
        sys.exit(1)

    # Check Ollama
    if not check_ollama_running():
        print("Starting Ollama...")
        subprocess.Popen(['ollama', 'serve'],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
        time.sleep(3)

    # Test phi:q4
    print("Testing phi:q4 model...")
    try:
        result = subprocess.run(['ollama', 'run', 'phi:q4', 'hello'],
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ phi:q4 responding")
        else:
            print("❌ phi:q4 not responding")
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print("❌ phi:q4 timeout")
        sys.exit(1)

    print("🎉 System ready!")

if __name__ == "__main__":
    main()