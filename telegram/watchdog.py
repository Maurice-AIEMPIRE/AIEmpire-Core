#!/usr/bin/env python3
"""
GALAXIA WATCHDOG - System Health Monitor & Auto-Restart
Monitors all services (Ollama, Redis, PostgreSQL, Neo4j, Bots)
Automatically restarts failed services and alerts on critical issues
"""

import asyncio
import json
import logging
import os
import subprocess
import psutil
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

from redis_state import StateStore

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser("~/galaxia-watchdog.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

WATCHDOG_ID = f"watchdog-{os.getenv('HOSTNAME', 'unknown')}"


class ServiceMonitor:
    """Monitor and manage Galaxia OS services"""

    # Service definitions: (name, check_command, restart_command)
    SERVICES = {
        "redis": {
            "check": "redis-cli ping",
            "restart": "systemctl restart redis-server",
            "critical": True,
        },
        "ollama": {
            "check": "curl -s http://localhost:11434/api/tags",
            "restart": "systemctl restart ollama",
            "critical": False,
        },
        "bot": {
            "check": "systemctl is-active --quiet galaxia-bot",
            "restart": "systemctl restart galaxia-bot",
            "critical": True,
        },
        "orchestrator": {
            "check": "systemctl is-active --quiet galaxia-orchestrator",
            "restart": "systemctl restart galaxia-orchestrator",
            "critical": True,
        },
    }

    def __init__(self):
        self.state_store = StateStore()
        self.service_status = {}
        self.error_counts = {}
        logger.info(f"🐕 Watchdog initialized: {WATCHDOG_ID}")

    def check_service(self, service_name: str) -> bool:
        """Check if service is healthy"""
        service = self.SERVICES.get(service_name)
        if not service:
            return False

        try:
            result = subprocess.run(
                service["check"],
                shell=True,
                capture_output=True,
                timeout=5
            )
            is_healthy = result.returncode == 0
            logger.debug(f"Check {service_name}: {'✅' if is_healthy else '❌'}")
            return is_healthy
        except subprocess.TimeoutExpired:
            logger.warning(f"⏱️ Check timeout for {service_name}")
            return False
        except Exception as e:
            logger.error(f"❌ Check failed for {service_name}: {e}")
            return False

    async def restart_service(self, service_name: str) -> bool:
        """Attempt to restart failed service"""
        service = self.SERVICES.get(service_name)
        if not service:
            return False

        logger.info(f"🔄 Attempting to restart {service_name}...")

        try:
            result = subprocess.run(
                service["restart"],
                shell=True,
                capture_output=True,
                timeout=30,
                check=False
            )

            await asyncio.sleep(2)
            is_healthy = self.check_service(service_name)

            if is_healthy:
                logger.info(f"✅ Successfully restarted {service_name}")
                self.error_counts[service_name] = 0
                return True
            else:
                logger.error(f"❌ {service_name} still unhealthy after restart")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"⏱️ Restart timeout for {service_name}")
            return False
        except Exception as e:
            logger.error(f"❌ Restart failed for {service_name}: {e}")
            return False

    def get_system_metrics(self) -> Dict[str, float]:
        """Get CPU, RAM, Disk metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "cpu_percent": cpu_percent,
                "mem_percent": mem.percent,
                "mem_available": mem.available / (1024**3),  # GB
                "disk_percent": disk.percent,
            }
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {}

    async def check_all_services(self) -> Dict[str, Dict]:
        """Check all services and return status"""
        status = {}

        for service_name in self.SERVICES.keys():
            is_healthy = self.check_service(service_name)
            status[service_name] = {"healthy": is_healthy}

            if not is_healthy:
                self.error_counts[service_name] = self.error_counts.get(service_name, 0) + 1

                # Restart critical services after 2 failures
                if self.SERVICES[service_name]["critical"] and self.error_counts[service_name] >= 2:
                    success = await self.restart_service(service_name)
                    status[service_name]["restarted"] = success

        return status

    def check_bot_heartbeats(self) -> List[str]:
        """Check which bot instances are still alive"""
        active_bots = self.state_store.get_active_bots()
        return active_bots

    async def run(self) -> None:
        """Main watchdog loop"""
        logger.info(f"🐕 Watchdog loop starting: {WATCHDOG_ID}")

        while True:
            try:
                # Check all services
                service_status = await self.check_all_services()

                # Get metrics
                metrics = self.get_system_metrics()
                self.state_store.set_system_metric("cpu_percent", metrics.get("cpu_percent", 0))
                self.state_store.set_system_metric("mem_percent", metrics.get("mem_percent", 0))

                # Check bot heartbeats
                active_bots = self.check_bot_heartbeats()

                # Log status
                logger.info(f"""
🐕 WATCHDOG STATUS
Services: {json.dumps(service_status, indent=2)}
Metrics: CPU={metrics.get('cpu_percent', 0):.1f}%, RAM={metrics.get('mem_percent', 0):.1f}%
Active Bots: {len(active_bots)} ({', '.join(active_bots[:3]) if active_bots else 'None'})
""")

                # Alert on critical issues
                if metrics.get("cpu_percent", 0) > 90:
                    logger.warning(f"⚠️ CRITICAL: CPU at {metrics.get('cpu_percent', 0):.1f}%")
                if metrics.get("mem_percent", 0) > 92:
                    logger.warning(f"⚠️ CRITICAL: RAM at {metrics.get('mem_percent', 0):.1f}%")

                # Wait before next check
                await asyncio.sleep(30)

            except KeyboardInterrupt:
                logger.info("🛑 Watchdog stopping...")
                break
            except Exception as e:
                logger.error(f"❌ Watchdog error: {e}")
                await asyncio.sleep(10)


async def main():
    """Main entry point"""
    monitor = ServiceMonitor()
    try:
        await monitor.run()
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
