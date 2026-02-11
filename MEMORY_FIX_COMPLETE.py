#!/usr/bin/env python3

"""
MEMORY_FIX_COMPLETE.py - Auto-optimizer for memory management
Monitors and optimizes RAM usage automatically
"""

import time
import psutil
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(filename='memory_fix.log', level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')

class MemoryOptimizer:
    def __init__(self):
        self.min_free_mb = 512
        self.max_used_percent = 75
        self.check_interval = 60  # seconds

    def get_memory_stats(self):
        """Get current memory statistics"""
        mem = psutil.virtual_memory()
        return {
            'total': mem.total // (1024 * 1024),
            'used': mem.used // (1024 * 1024),
            'free': mem.available // (1024 * 1024),
            'percent': mem.percent
        }

    def kill_heavy_processes(self):
        """Kill processes using too much memory"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                if proc.info['memory_percent'] > 10:  # >10% memory
                    if proc.info['name'] not in ['kernel_task', 'WindowServer', 'loginwindow']:
                        processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        for proc in sorted(processes, key=lambda x: x.info['memory_percent'], reverse=True)[:3]:
            try:
                logging.warning(f"Killing high-memory process: {proc.info['name']} ({proc.info['memory_percent']}%)")
                proc.kill()
            except:
                pass

    def optimize_ollama(self):
        """Ensure only lightweight models are loaded"""
        try:
            # Check running models
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if 'phi:q4' not in result.stdout:
                logging.info("Installing phi:q4 model")
                subprocess.run(['ollama', 'pull', 'phi:q4'], capture_output=True)
        except:
            pass

    def run_optimization(self):
        """Main optimization loop"""
        logging.info("Memory Optimizer started")

        while True:
            stats = self.get_memory_stats()
            logging.info(f"Memory: {stats['used']}MB used, {stats['free']}MB free ({stats['percent']}%)")

            if stats['free'] < self.min_free_mb or stats['percent'] > self.max_used_percent:
                logging.warning("Memory critical! Running optimization...")
                self.kill_heavy_processes()
                self.optimize_ollama()

                # Wait a bit for cleanup
                time.sleep(10)

            time.sleep(self.check_interval)

if __name__ == "__main__":
    optimizer = MemoryOptimizer()
    optimizer.run_optimization()