#!/usr/bin/env python3
import psutil
import subprocess
import sys

RAM_FREE = psutil.virtual_memory().available / (1024**3)
RAM_TOTAL = psutil.virtual_memory().total / (1024**3)
RAM_PCT = psutil.virtual_memory().percent

print(f"RAM: {RAM_FREE:.2f}GB free ({RAM_PCT:.0f}% used)")

if RAM_PCT > 85:
    print("ERROR: System RAM too low! Aborting.")
    print(f"Free: {RAM_FREE:.2f}GB / Total: {RAM_TOTAL:.2f}GB")
    print("Suggestions:")
    print("  1. Close other programs")
    print("  2. Use quantized models (q4)")
    print("  3. Check memory_monitor.sh")
    sys.exit(1)

# Launch with limited threads
import os
os.environ['OLLAMA_NUM_PARALLEL'] = '1'
os.environ['OLLAMA_NUM_THREAD'] = '2'

print("Starting Ollama...")
subprocess.run(['ollama', 'serve'])
