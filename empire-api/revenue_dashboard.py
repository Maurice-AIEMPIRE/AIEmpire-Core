#!/usr/bin/env python3
"""
Revenue Dashboard & System Health Check Script
Comprehensive monitoring for Maurice's AI Empire

Features:
- Gumroad API sales tracking (if API key available)
- System health checks (n8n, Redis, PostgreSQL, Ollama, OpenClaw)
- Resource monitoring (CPU, RAM, Disk)
- Revenue metrics (Today, Week, Month, Year)
- CRM lead metrics
- Kimi API usage tracking
- Beautiful colored CLI output
- JSON export for integration

Usage:
    python revenue_dashboard.py                    # Full dashboard
    python revenue_dashboard.py --json             # JSON output
    python revenue_dashboard.py --health-only      # Only health checks
    python revenue_dashboard.py --revenue-only     # Only revenue
    python revenue_dashboard.py --export out.json  # Export to file

Environment Variables:
    GUMROAD_TOKEN           - Gumroad API token for sales data
    KIMI_API_KEY           - Kimi API key for budget tracking
    POSTGRES_URL           - PostgreSQL connection string
    REDIS_HOST, REDIS_PORT - Redis connection details
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import os
import psutil
import shutil
from pathlib import Path
import subprocess
from functools import wraps
from dataclasses import dataclass, asdict
import argparse
from enum import Enum

try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    import redis
except ImportError:
    redis = None

try:
    import psycopg2
except ImportError:
    psycopg2 = None


class Colors:
    """ANSI color codes for CLI output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'

    @staticmethod
    def colorize(text: str, color: str) -> str:
        """Apply color to text"""
        return f"{color}{text}{Colors.RESET}"


class HealthStatus(Enum):
    """System health status"""
    UP = "UP"
    DOWN = "DOWN"
    UNKNOWN = "UNKNOWN"
    DEGRADED = "DEGRADED"


@dataclass
class ServiceHealth:
    """Service health status"""
    name: str
    status: HealthStatus
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    port: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'status': self.status.value,
            'response_time_ms': self.response_time_ms,
            'error': self.error_message,
            'port': self.port
        }


@dataclass
class ResourceMetrics:
    """System resource metrics"""
    cpu_percent: float
    ram_percent: float
    disk_percent: float
    disk_free_gb: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RevenueMetrics:
    """Revenue metrics summary"""
    today: float
    week: float
    month: float
    year: float
    total_sales: int
    total_revenue: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DashboardCollector:
    """Collect metrics from all sources"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.errors = []

    async def check_service_http(
        self,
        name: str,
        host: str,
        port: int,
        path: str = "/"
    ) -> ServiceHealth:
        """Check service health via HTTP"""
        url = f"http://{host}:{port}{path}"
        start = datetime.now()

        try:
            if aiohttp is None:
                return ServiceHealth(
                    name=name,
                    status=HealthStatus.UNKNOWN,
                    error_message="aiohttp not installed"
                )

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as resp:
                        response_time = (datetime.now() - start).total_seconds() * 1000
                        status = HealthStatus.UP if resp.status < 500 else HealthStatus.DEGRADED
                        return ServiceHealth(
                            name=name,
                            status=status,
                            response_time_ms=response_time,
                            port=port
                        )
                except asyncio.TimeoutError:
                    return ServiceHealth(
                        name=name,
                        status=HealthStatus.DOWN,
                        error_message="Request timeout",
                        port=port
                    )
        except Exception as e:
            return ServiceHealth(
                name=name,
                status=HealthStatus.DOWN,
                error_message=str(e),
                port=port
            )

    def check_service_tcp(self, name: str, host: str, port: int) -> ServiceHealth:
        """Check service availability via TCP socket"""
        import socket
        start = datetime.now()

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()

            response_time = (datetime.now() - start).total_seconds() * 1000

            if result == 0:
                return ServiceHealth(
                    name=name,
                    status=HealthStatus.UP,
                    response_time_ms=response_time,
                    port=port
                )
            else:
                return ServiceHealth(
                    name=name,
                    status=HealthStatus.DOWN,
                    error_message=f"Connection refused (errno {result})",
                    port=port
                )
        except Exception as e:
            return ServiceHealth(
                name=name,
                status=HealthStatus.DOWN,
                error_message=str(e),
                port=port
            )

    async def check_all_services(self) -> Dict[str, ServiceHealth]:
        """Check all system services"""
        services = {
            'n8n': ('localhost', 5678, 'http'),
            'Redis': ('localhost', 6379, 'tcp'),
            'PostgreSQL': ('localhost', 5432, 'tcp'),
            'Ollama': ('localhost', 11434, 'http'),
            'OpenClaw': ('localhost', 18789, 'http'),
        }

        results = {}
        tasks = []

        for name, (host, port, protocol) in services.items():
            if protocol == 'http':
                task = self.check_service_http(name, host, port, '/health')
                tasks.append(task)
            else:
                # TCP checks are synchronous
                results[name] = self.check_service_tcp(name, host, port)

        # Execute async HTTP checks
        if tasks:
            http_results = await asyncio.gather(*tasks, return_exceptions=True)
            http_services = list(services.items())
            http_idx = 0
            for name, (host, port, protocol) in http_services:
                if protocol == 'http':
                    result = http_results[http_idx]
                    if isinstance(result, ServiceHealth):
                        results[name] = result
                    else:
                        results[name] = ServiceHealth(
                            name=name,
                            status=HealthStatus.UNKNOWN,
                            error_message=str(result) if result else "Unknown error"
                        )
                    http_idx += 1

        return results

    def get_resource_metrics(self) -> ResourceMetrics:
        """Get system resource usage"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        ram_percent = psutil.virtual_memory().percent

        disk_usage = shutil.disk_usage('/')
        disk_percent = (disk_usage.used / disk_usage.total) * 100
        disk_free_gb = disk_usage.free / (1024**3)

        return ResourceMetrics(
            cpu_percent=cpu_percent,
            ram_percent=ram_percent,
            disk_percent=disk_percent,
            disk_free_gb=round(disk_free_gb, 2),
            timestamp=datetime.now().isoformat()
        )

    async def check_gumroad_sales(self) -> Optional[RevenueMetrics]:
        """Check Gumroad API for sales data"""
        token = os.getenv('GUMROAD_TOKEN')
        if not token:
            return None

        if aiohttp is None:
            return None

        try:
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {token}'}
                async with session.get(
                    'https://api.gumroad.com/v2/sales',
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        sales = data.get('sales', [])
                        return self._process_gumroad_sales(sales)
        except Exception as e:
            if self.verbose:
                self.errors.append(f"Gumroad API error: {e}")

        return None

    def _process_gumroad_sales(self, sales: list) -> RevenueMetrics:
        """Process Gumroad sales data into metrics"""
        now = datetime.now()
        today = now.date()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        year_ago = now - timedelta(days=365)

        today_total = 0.0
        week_total = 0.0
        month_total = 0.0
        year_total = 0.0
        total_revenue = 0.0

        for sale in sales:
            try:
                amount = float(sale.get('price', 0))
                timestamp = datetime.fromisoformat(sale.get('created_at', '').replace('Z', '+00:00'))

                total_revenue += amount

                if timestamp.date() == today:
                    today_total += amount

                if timestamp >= week_ago:
                    week_total += amount

                if timestamp >= month_ago:
                    month_total += amount

                if timestamp >= year_ago:
                    year_total += amount
            except (ValueError, TypeError):
                continue

        return RevenueMetrics(
            today=round(today_total, 2),
            week=round(week_total, 2),
            month=round(month_total, 2),
            year=round(year_total, 2),
            total_sales=len(sales),
            total_revenue=round(total_revenue, 2),
            timestamp=datetime.now().isoformat()
        )

    def get_kimi_api_budget(self) -> Optional[Dict[str, Any]]:
        """Get Kimi API budget info"""
        api_key = os.getenv('KIMI_API_KEY')
        if not api_key:
            return None

        # This would require actual Kimi API call
        # For now, return placeholder
        return {
            'api_key_available': bool(api_key),
            'budget': 'N/A - requires API call',
            'note': 'Implement actual Kimi API integration'
        }

    async def check_crm_leads(self) -> Optional[Dict[str, Any]]:
        """Check CRM lead metrics"""
        try:
            # Try to connect to CRM API (port 3500)
            health = await self.check_service_http('CRM', 'localhost', 3500, '/api/health')

            if health.status == HealthStatus.UP:
                # Would fetch actual lead data here
                return {
                    'status': 'UP',
                    'leads_today': 0,
                    'leads_week': 0,
                    'leads_month': 0,
                    'conversion_rate': 0.0,
                    'note': 'Implement actual CRM API integration'
                }
        except Exception as e:
            if self.verbose:
                self.errors.append(f"CRM check error: {e}")

        return None


class DashboardFormatter:
    """Format and display dashboard output"""

    @staticmethod
    def print_header(title: str) -> None:
        """Print a formatted header"""
        print(f"\n{Colors.colorize('━' * 80, Colors.BLUE)}")
        print(f"{Colors.colorize(title, Colors.BOLD + Colors.CYAN)}")
        print(f"{Colors.colorize('━' * 80, Colors.BLUE)}\n")

    @staticmethod
    def print_section(title: str) -> None:
        """Print a section header"""
        print(f"{Colors.colorize(f'▸ {title}', Colors.BOLD + Colors.YELLOW)}")

    @staticmethod
    def print_service_health(services: Dict[str, ServiceHealth]) -> None:
        """Print service health status"""
        DashboardFormatter.print_section("System Services")

        for name, health in services.items():
            status_color = {
                HealthStatus.UP: Colors.GREEN,
                HealthStatus.DOWN: Colors.RED,
                HealthStatus.DEGRADED: Colors.YELLOW,
                HealthStatus.UNKNOWN: Colors.MAGENTA,
            }.get(health.status, Colors.WHITE)

            status_text = Colors.colorize(health.status.value, status_color)

            if health.response_time_ms:
                details = f"({health.response_time_ms:.1f}ms)"
            elif health.error_message:
                details = f"({health.error_message})"
            else:
                details = ""

            port_str = f":{health.port}" if health.port else ""
            print(f"  {name:15} {status_text:15} {details}")

        print()

    @staticmethod
    def print_resource_metrics(metrics: ResourceMetrics) -> None:
        """Print resource usage metrics"""
        DashboardFormatter.print_section("System Resources")

        cpu_color = Colors.RED if metrics.cpu_percent > 80 else (Colors.YELLOW if metrics.cpu_percent > 60 else Colors.GREEN)
        ram_color = Colors.RED if metrics.ram_percent > 85 else (Colors.YELLOW if metrics.ram_percent > 70 else Colors.GREEN)
        disk_color = Colors.RED if metrics.disk_percent > 90 else (Colors.YELLOW if metrics.disk_percent > 75 else Colors.GREEN)

        cpu_bar = DashboardFormatter._create_bar(metrics.cpu_percent, cpu_color)
        ram_bar = DashboardFormatter._create_bar(metrics.ram_percent, ram_color)
        disk_bar = DashboardFormatter._create_bar(metrics.disk_percent, disk_color)

        print(f"  CPU   {cpu_bar} {metrics.cpu_percent:5.1f}%")
        print(f"  RAM   {ram_bar} {metrics.ram_percent:5.1f}%")
        print(f"  DISK  {disk_bar} {metrics.disk_percent:5.1f}% ({metrics.disk_free_gb:.1f} GB free)")
        print()

    @staticmethod
    def _create_bar(percent: float, color: str, width: int = 20) -> str:
        """Create a visual progress bar"""
        filled = int((percent / 100) * width)
        empty = width - filled
        bar = '█' * filled + '░' * empty
        return Colors.colorize(f"[{bar}]", color)

    @staticmethod
    def print_revenue_metrics(metrics: Optional[RevenueMetrics]) -> None:
        """Print revenue metrics"""
        DashboardFormatter.print_section("Revenue Metrics")

        if metrics is None:
            print("  " + Colors.colorize("No revenue data available", Colors.YELLOW))
            print()
            return

        print(f"  Today        {Colors.colorize(f'€{metrics.today:>10.2f}', Colors.GREEN)}")
        print(f"  Week         {Colors.colorize(f'€{metrics.week:>10.2f}', Colors.GREEN)}")
        print(f"  Month        {Colors.colorize(f'€{metrics.month:>10.2f}', Colors.GREEN)}")
        print(f"  Year         {Colors.colorize(f'€{metrics.year:>10.2f}', Colors.GREEN)}")
        print(f"  Total        {Colors.colorize(f'€{metrics.total_revenue:>10.2f}', Colors.BOLD + Colors.GREEN)}")
        print(f"  Sales Count  {Colors.colorize(f'{metrics.total_sales:>10}', Colors.CYAN)}")
        print()

    @staticmethod
    def print_kimi_budget(budget_data: Optional[Dict[str, Any]]) -> None:
        """Print Kimi API budget"""
        DashboardFormatter.print_section("Kimi API Budget")

        if budget_data is None:
            print("  " + Colors.colorize("No Kimi API key configured", Colors.YELLOW))
            print()
            return

        print(f"  API Key Available  {Colors.colorize(str(budget_data.get('api_key_available')), Colors.CYAN)}")
        print(f"  Budget             {Colors.colorize(str(budget_data.get('budget')), Colors.YELLOW)}")
        print()

    @staticmethod
    def print_crm_leads(leads_data: Optional[Dict[str, Any]]) -> None:
        """Print CRM lead metrics"""
        DashboardFormatter.print_section("CRM Leads")

        if leads_data is None:
            print("  " + Colors.colorize("CRM not available", Colors.YELLOW))
            print()
            return

        print(f"  Today        {leads_data.get('leads_today', 0):>10}")
        print(f"  Week         {leads_data.get('leads_week', 0):>10}")
        print(f"  Month        {leads_data.get('leads_month', 0):>10}")
        print(f"  Conversion   {leads_data.get('conversion_rate', 0):>9.1f}%")
        print()

    @staticmethod
    def print_summary(services: Dict[str, ServiceHealth], resources: ResourceMetrics) -> None:
        """Print overall summary"""
        DashboardFormatter.print_section("Summary")

        services_up = sum(1 for s in services.values() if s.status == HealthStatus.UP)
        total_services = len(services)

        health_status = Colors.colorize("HEALTHY", Colors.GREEN) if services_up == total_services else Colors.colorize("DEGRADED", Colors.YELLOW)

        print(f"  Overall Health     {health_status}")
        print(f"  Services           {services_up}/{total_services} UP")
        print(f"  Timestamp          {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()


class RevenueCommandLine:
    """CLI entry point"""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            description='Maurice\'s AI Empire - Revenue Dashboard & System Health',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python revenue_dashboard.py                    # Full dashboard
  python revenue_dashboard.py --json             # JSON output only
  python revenue_dashboard.py --health-only      # Only health checks
  python revenue_dashboard.py --revenue-only     # Only revenue metrics
  python revenue_dashboard.py --export report.json  # Export to file
            """
        )

        parser.add_argument(
            '--json',
            action='store_true',
            help='Output as JSON instead of formatted text'
        )
        parser.add_argument(
            '--health-only',
            action='store_true',
            help='Only check system health'
        )
        parser.add_argument(
            '--revenue-only',
            action='store_true',
            help='Only show revenue metrics'
        )
        parser.add_argument(
            '--export',
            type=str,
            metavar='FILE',
            help='Export results to JSON file'
        )
        parser.add_argument(
            '-v', '--verbose',
            action='store_true',
            help='Verbose output with error details'
        )

        return parser

    async def run(self) -> int:
        """Run the dashboard"""
        args = self.parser.parse_args()

        collector = DashboardCollector(verbose=args.verbose)

        # Collect data
        services = await collector.check_all_services()
        resources = collector.get_resource_metrics()
        revenue = await collector.check_gumroad_sales() if not args.health_only else None
        kimi_budget = collector.get_kimi_api_budget() if not args.health_only else None
        crm_leads = await collector.check_crm_leads() if not args.health_only else None

        # Prepare output
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'services': {name: health.to_dict() for name, health in services.items()},
            'resources': resources.to_dict(),
        }

        if revenue:
            output_data['revenue'] = revenue.to_dict()
        if kimi_budget:
            output_data['kimi'] = kimi_budget
        if crm_leads:
            output_data['crm'] = crm_leads

        # Output
        if args.json or args.export:
            json_output = json.dumps(output_data, indent=2)

            if args.json:
                print(json_output)

            if args.export:
                Path(args.export).write_text(json_output)
                print(f"Exported to {args.export}", file=sys.stderr)
        else:
            DashboardFormatter.print_header("MAURICE'S AI EMPIRE - SYSTEM DASHBOARD")

            if not args.revenue_only:
                DashboardFormatter.print_service_health(services)
                DashboardFormatter.print_resource_metrics(resources)

            if not args.health_only:
                DashboardFormatter.print_revenue_metrics(revenue)
                DashboardFormatter.print_kimi_budget(kimi_budget)
                DashboardFormatter.print_crm_leads(crm_leads)

            if not args.revenue_only and not args.health_only:
                DashboardFormatter.print_summary(services, resources)

        # Return exit code based on health
        services_up = sum(1 for s in services.values() if s.status == HealthStatus.UP)
        if services_up < len(services):
            return 1
        return 0


async def main():
    """Main entry point"""
    cli = RevenueCommandLine()
    exit_code = await cli.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    asyncio.run(main())
