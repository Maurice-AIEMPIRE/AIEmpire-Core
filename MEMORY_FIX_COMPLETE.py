#!/usr/bin/env python3
"""
COMPLETE MEMORY FIX FOR LOW-RAM SYSTEM (3.8GB)
Aggressive Memory Management + Resource Monitoring
For: Maurice's Mac M1+ / Linux VM with 3.8GB RAM
"""

import os
import sys
import psutil
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

class MemoryFixer:
    def __init__(self):
        self.ram_total_gb = psutil.virtual_memory().total / (1024**3)
        self.ram_available_gb = psutil.virtual_memory().available / (1024**3)
        self.ram_used_gb = psutil.virtual_memory().used / (1024**3)
        self.log_file = Path('memory_fix.log')

    def log(self, msg, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] [{level}] {msg}"
        print(log_msg)
        with open(self.log_file, 'a') as f:
            f.write(log_msg + "\n")

    def print_status(self):
        print("\n" + "="*60)
        print("SYSTEM MEMORY STATUS")
        print("="*60)
        print(f"Total RAM:      {self.ram_total_gb:.2f} GB")
        print(f"Used RAM:       {self.ram_used_gb:.2f} GB ({psutil.virtual_memory().percent}%)")
        print(f"Available RAM:  {self.ram_available_gb:.2f} GB")
        status = 'CRITICAL' if self.ram_available_gb < 0.5 else 'WARNING' if self.ram_available_gb < 1.0 else 'OK'
        print(f"Status:         {status}")
        print("="*60 + "\n")

    def kill_memory_hogs(self):
        self.log("Scanning for memory hogs...", "SCAN")
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                mem_pct = proc.info['memory_percent']
                if mem_pct > 5:
                    name = proc.info['name']
                    pid = proc.info['pid']
                    skip_procs = ['systemd', 'kernel', 'init', 'bash', 'zsh', 'ssh']
                    if any(skip in name for skip in skip_procs):
                        continue
                    self.log(f"Found hog: {name} (PID {pid}) using {mem_pct:.1f}%", "WARN")
                    if self.ram_available_gb < 0.3:
                        self.log(f"KILLING: {name} (critical RAM)", "ERROR")
                        try:
                            os.kill(pid, 9)
                        except:
                            pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    def optimize_ollama_config(self):
        self.log("Optimizing Ollama configuration...", "CONFIG")
        ollama_config = {
            "OLLAMA_NUM_PARALLEL": 1,
            "OLLAMA_NUM_THREAD": 2,
            "OLLAMA_KEEP_ALIVE": "5m",
        }
        config_lines = "\n".join([f"export {k}={v}" for k, v in ollama_config.items()])
        shells = [Path.home() / '.bashrc', Path.home() / '.zshrc']
        for shell_rc in shells:
            if shell_rc.exists():
                content = shell_rc.read_text()
                if "OLLAMA_NUM_PARALLEL" not in content:
                    with open(shell_rc, 'a') as f:
                        f.write(f"\n# OLLAMA Memory Optimization\n{config_lines}\n")
                    self.log(f"Updated {shell_rc}", "SUCCESS")
        self.log("Ollama configured for low-RAM system", "SUCCESS")

    def recommend_modelle(self):
        self.log("MODELL-EMPFEHLUNGEN FUER 3.8GB RAM", "INFO")
        self.log("BEST: phi:q4 (600MB) oder neural-chat:q4 (2.5GB)", "RECOMMEND")

    def generate_fix_report(self):
        report = f"MEMORY FIX COMPLETE - Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        print(report)
        self.log("Fix report generated", "SUCCESS")

def main():
    print("\n" + "="*60)
    print("STARTING COMPLETE MEMORY FIX")
    print("="*60 + "\n")
    fixer = MemoryFixer()
    fixer.print_status()
    print("Step 1: Killing memory hogs...")
    fixer.kill_memory_hogs()
    print("\nStep 2: Optimizing Ollama configuration...")
    fixer.optimize_ollama_config()
    print("\nStep 3: Model recommendations...")
    fixer.recommend_modelle()
    print("\nStep 4: Generating report...")
    fixer.generate_fix_report()
    print("\n" + "="*60)
    print("MEMORY FIX COMPLETE!")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
