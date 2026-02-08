#!/usr/bin/env python3
"""
Mission Control Scanner - Scans all active & open tasks across AI Empire systems
Generates ONE-PAGE mission control overview with priorities, blockers, and action items.

Scans:
- OpenClaw jobs/config
- Git/GitHub issues & PRs
- Docker compose stacks
- n8n workflows
- Agent queues
- Brain system sessions
- Atomic reactor tasks/reports
- Backlogs and logs
"""

import json
import os
import subprocess
import yaml
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import glob

# Categories for task clustering
CATEGORIES = ["BUILD", "FIX", "AUTOMATE", "CONTENT", "STRATEGY"]

# Prioritization weights
PRIORITY_WEIGHTS = {
    "IMPACT": 5,
    "URGENCY": 3,
    "EFFORT": -2  # Lower effort is better
}


class TaskScanner:
    """Scans all systems for active tasks"""
    
    def __init__(self, base_path: str = None):
        self.base_path = base_path or os.getcwd()
        self.tasks = []
        self.stats = {
            "total_open": 0,
            "by_category": defaultdict(int),
            "cost_risks": [],
            "blockers": [],
            "levers": [],
            "time_critical": []
        }
    
    def scan_all(self) -> Dict[str, Any]:
        """Execute full system scan"""
        print("🔍 Scanning ALL systems...")
        
        self._scan_openclaw()
        self._scan_github()
        self._scan_docker()
        self._scan_n8n()
        self._scan_atomic_reactor()
        self._scan_brain_system()
        self._scan_crm()
        self._scan_logs()
        
        self._categorize_tasks()
        self._analyze_stats()
        
        return {
            "tasks": self.tasks,
            "stats": self.stats,
            "scan_time": datetime.now().isoformat()
        }
    
    def _scan_openclaw(self):
        """Scan OpenClaw configuration and jobs"""
        openclaw_path = Path(self.base_path) / "openclaw-config"
        if not openclaw_path.exists():
            return
        
        # Scan jobs.json
        jobs_file = openclaw_path / "jobs.json"
        if jobs_file.exists():
            try:
                with open(jobs_file) as f:
                    jobs = json.load(f)
                    for job in jobs.get("jobs", []):
                        if job.get("status") in ["pending", "running", "queued"]:
                            self.tasks.append({
                                "id": f"openclaw-{job.get('id', 'unknown')}",
                                "title": job.get("name", "OpenClaw Job"),
                                "source": "OpenClaw",
                                "status": job.get("status", "unknown"),
                                "category": self._infer_category(job.get("name", "")),
                                "impact": job.get("priority", 5),
                                "urgency": 5 if job.get("status") == "running" else 3,
                                "effort": 5,
                                "details": job
                            })
            except Exception as e:
                print(f"  ⚠️  OpenClaw scan error: {e}")
    
    def _scan_github(self):
        """Scan GitHub issues and PRs"""
        try:
            # Get open issues
            result = subprocess.run(
                ["git", "log", "--oneline", "-n", "10"],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                commits = result.stdout.strip().split("\n")
                # Check for any pending work mentioned in commits
                for commit in commits[:5]:
                    if any(word in commit.lower() for word in ["todo", "wip", "pending", "fix"]):
                        self.tasks.append({
                            "id": f"git-{commit[:7]}",
                            "title": commit[8:60] if len(commit) > 8 else commit,
                            "source": "Git",
                            "status": "pending",
                            "category": self._infer_category(commit),
                            "impact": 5,
                            "urgency": 7,
                            "effort": 3,
                            "details": {"commit": commit}
                        })
        except Exception as e:
            print(f"  ⚠️  GitHub scan error: {e}")
    
    def _scan_docker(self):
        """Scan Docker compose configurations"""
        compose_files = [
            Path(self.base_path) / "systems" / "docker-compose.yaml",
            Path(self.base_path) / "atomic-reactor" / "docker-compose.yaml",
            Path(self.base_path) / "openclaw-config" / "docker-compose.yaml"
        ]
        
        for compose_file in compose_files:
            if compose_file.exists():
                try:
                    with open(compose_file) as f:
                        config = yaml.safe_load(f)
                        services = config.get("services", {})
                        for service_name, service_config in services.items():
                            # Check for running services (assume they're tasks)
                            self.tasks.append({
                                "id": f"docker-{service_name}",
                                "title": f"Docker Service: {service_name}",
                                "source": "Docker",
                                "status": "running",
                                "category": "AUTOMATE",
                                "impact": 6,
                                "urgency": 4,
                                "effort": 2,
                                "details": {
                                    "image": service_config.get("image"),
                                    "ports": service_config.get("ports", [])
                                }
                            })
                            
                            # Flag cost risks
                            if "ollama" in service_name or "claude" in service_name:
                                self.stats["cost_risks"].append({
                                    "service": service_name,
                                    "type": "Compute",
                                    "risk": "Medium"
                                })
                except Exception as e:
                    print(f"  ⚠️  Docker scan error ({compose_file}): {e}")
    
    def _scan_n8n(self):
        """Scan n8n workflow configurations"""
        n8n_path = Path(self.base_path) / "n8n-workflows"
        if not n8n_path.exists():
            return
        
        workflow_files = list(n8n_path.glob("*.json"))
        for wf_file in workflow_files:
            try:
                with open(wf_file) as f:
                    workflow = json.load(f)
                    wf_name = workflow.get("name", wf_file.stem)
                    self.tasks.append({
                        "id": f"n8n-{wf_file.stem}",
                        "title": f"n8n Workflow: {wf_name}",
                        "source": "n8n",
                        "status": "active",
                        "category": "AUTOMATE",
                        "impact": 7,
                        "urgency": 5,
                        "effort": 3,
                        "details": {
                            "nodes": len(workflow.get("nodes", [])),
                            "file": wf_file.name
                        }
                    })
            except Exception as e:
                print(f"  ⚠️  n8n scan error ({wf_file}): {e}")
    
    def _scan_atomic_reactor(self):
        """Scan Atomic Reactor tasks and reports"""
        reactor_path = Path(self.base_path) / "atomic-reactor"
        
        # Scan task files
        tasks_path = reactor_path / "tasks"
        if tasks_path.exists():
            task_files = list(tasks_path.glob("*.yaml")) + list(tasks_path.glob("*.yml"))
            for task_file in task_files:
                # Skip hidden files (._*)
                if task_file.name.startswith("._"):
                    continue
                try:
                    with open(task_file) as f:
                        task_data = yaml.safe_load(f)
                        if task_data:
                            self.tasks.append({
                                "id": f"reactor-{task_file.stem}",
                                "title": task_data.get("name", task_file.stem),
                                "source": "AtomicReactor",
                                "status": task_data.get("status", "pending"),
                                "category": self._infer_category(task_data.get("name", "")),
                                "impact": task_data.get("priority", 5),
                                "urgency": 6,
                                "effort": task_data.get("effort", 5),
                                "details": task_data
                            })
                            
                            # Check for cost risks
                            if task_data.get("tokens", 0) > 50000:
                                self.stats["cost_risks"].append({
                                    "task": task_data.get("name"),
                                    "type": "Token",
                                    "risk": "High",
                                    "tokens": task_data.get("tokens")
                                })
                except Exception as e:
                    print(f"  ⚠️  Reactor task scan error ({task_file}): {e}")
        
        # Scan reports
        reports_path = reactor_path / "reports"
        if reports_path.exists():
            report_files = list(reports_path.glob("*.json"))[-5:]  # Last 5 reports
            for report_file in report_files:
                try:
                    with open(report_file) as f:
                        report = json.load(f)
                        # Check for failures or warnings
                        if report.get("status") in ["failed", "error"]:
                            self.stats["blockers"].append({
                                "task": report.get("task_id"),
                                "reason": report.get("error", "Unknown error"),
                                "source": "AtomicReactor"
                            })
                except Exception as e:
                    print(f"  ⚠️  Reactor report scan error: {e}")
    
    def _scan_brain_system(self):
        """Scan brain system orchestrator and sessions"""
        brain_path = Path(self.base_path) / "brain-system"
        
        # Check for orchestrator DB
        db_file = brain_path / "brain_state.db"
        if db_file.exists():
            try:
                conn = sqlite3.connect(str(db_file))
                cursor = conn.cursor()
                
                # Get active events/tasks from synapses table
                cursor.execute("""
                    SELECT event_type, source_brain, target_brain, priority, timestamp
                    FROM synapses 
                    WHERE processed = 0 
                    ORDER BY priority DESC 
                    LIMIT 20
                """)
                
                for row in cursor.fetchall():
                    event_type, source, target, priority, timestamp = row
                    self.tasks.append({
                        "id": f"brain-{source}-{target}",
                        "title": f"Brain Event: {event_type}",
                        "source": "BrainSystem",
                        "status": "queued",
                        "category": self._infer_category(event_type),
                        "impact": priority,
                        "urgency": 8,
                        "effort": 3,
                        "details": {
                            "from": source,
                            "to": target,
                            "timestamp": timestamp
                        }
                    })
                
                conn.close()
            except Exception as e:
                print(f"  ⚠️  Brain system scan error: {e}")
    
    def _scan_crm(self):
        """Scan CRM database for leads and deals"""
        crm_path = Path(self.base_path) / "crm"
        db_file = crm_path / "crm.db"
        
        if db_file.exists():
            try:
                conn = sqlite3.connect(str(db_file))
                cursor = conn.cursor()
                
                # Get active leads
                cursor.execute("""
                    SELECT id, company, contact_name, bant_score, stage, potential_revenue
                    FROM leads 
                    WHERE stage NOT IN ('closed_won', 'closed_lost')
                    ORDER BY bant_score DESC 
                    LIMIT 10
                """)
                
                for row in cursor.fetchall():
                    lead_id, company, contact, bant, stage, revenue = row
                    self.tasks.append({
                        "id": f"crm-lead-{lead_id}",
                        "title": f"Lead: {company} ({contact})",
                        "source": "CRM",
                        "status": stage,
                        "category": "CONTENT" if stage == "engagement" else "STRATEGY",
                        "impact": bant if bant else 5,
                        "urgency": 9 if stage == "negotiation" else 6,
                        "effort": 4,
                        "details": {
                            "company": company,
                            "bant": bant,
                            "revenue": revenue
                        }
                    })
                    
                    # High-value leads are levers
                    if revenue and revenue > 5000:
                        self.stats["levers"].append({
                            "task": f"Close lead: {company}",
                            "impact": f"€{revenue}",
                            "source": "CRM"
                        })
                
                conn.close()
            except Exception as e:
                print(f"  ⚠️  CRM scan error: {e}")
    
    def _scan_logs(self):
        """Scan various log files for errors and warnings"""
        log_patterns = [
            "*.log",
            "**/*.log",
            "logs/*.log"
        ]
        
        # Look for recent errors in logs
        for pattern in log_patterns:
            log_files = glob.glob(os.path.join(self.base_path, pattern), recursive=True)
            for log_file in log_files[:5]:  # Limit to 5 log files
                try:
                    # Check last 50 lines for errors
                    with open(log_file) as f:
                        lines = f.readlines()[-50:]
                        error_count = sum(1 for line in lines if "ERROR" in line or "FATAL" in line)
                        
                        if error_count > 0:
                            self.stats["blockers"].append({
                                "task": f"Log errors in {Path(log_file).name}",
                                "reason": f"{error_count} errors found",
                                "source": "Logs"
                            })
                except Exception as e:
                    pass  # Skip unreadable logs
    
    def _infer_category(self, text: str) -> str:
        """Infer task category from text"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["build", "create", "develop", "implement", "setup"]):
            return "BUILD"
        elif any(word in text_lower for word in ["fix", "bug", "error", "issue", "repair"]):
            return "FIX"
        elif any(word in text_lower for word in ["automate", "workflow", "pipeline", "deploy", "ci/cd"]):
            return "AUTOMATE"
        elif any(word in text_lower for word in ["content", "post", "write", "blog", "copy", "lead"]):
            return "CONTENT"
        elif any(word in text_lower for word in ["strategy", "plan", "analyze", "research", "revenue"]):
            return "STRATEGY"
        
        return "BUILD"  # Default
    
    def _normalize_value(self, value) -> int:
        """Normalize priority values to integers (1-10)"""
        if isinstance(value, int):
            return max(1, min(10, value))
        elif isinstance(value, str):
            value_lower = value.lower()
            if value_lower in ["critical", "high", "urgent"]:
                return 9
            elif value_lower in ["medium", "normal"]:
                return 5
            elif value_lower in ["low"]:
                return 3
            else:
                # Try to parse as int
                try:
                    return max(1, min(10, int(value)))
                except ValueError:
                    return 5  # Default
        else:
            return 5  # Default
    
    def _categorize_tasks(self):
        """Categorize and prioritize all tasks"""
        for task in self.tasks:
            # Ensure numeric values, handle strings
            impact = self._normalize_value(task.get("impact", 5))
            urgency = self._normalize_value(task.get("urgency", 5))
            effort = self._normalize_value(task.get("effort", 5))
            
            # Calculate priority score
            score = (
                impact * PRIORITY_WEIGHTS["IMPACT"] +
                urgency * PRIORITY_WEIGHTS["URGENCY"] +
                effort * PRIORITY_WEIGHTS["EFFORT"]
            )
            task["priority_score"] = score
            task["impact"] = impact
            task["urgency"] = urgency
            task["effort"] = effort
        
        # Sort by priority
        self.tasks.sort(key=lambda x: x["priority_score"], reverse=True)
        
        # Update stats
        self.stats["total_open"] = len(self.tasks)
        for task in self.tasks:
            self.stats["by_category"][task["category"]] += 1
    
    def _analyze_stats(self):
        """Analyze tasks for blockers, levers, and time-critical items"""
        # Identify top blockers (tasks with high urgency but dependencies)
        for task in self.tasks:
            if task["urgency"] >= 8 and task.get("status") in ["blocked", "error", "failed"]:
                if len(self.stats["blockers"]) < 10:
                    self.stats["blockers"].append({
                        "task": task["title"],
                        "reason": f"High urgency ({task['urgency']}) but {task['status']}",
                        "source": task["source"]
                    })
        
        # Identify top levers (high impact tasks)
        for task in self.tasks:
            if task["impact"] >= 8:
                if len(self.stats["levers"]) < 10:
                    self.stats["levers"].append({
                        "task": task["title"],
                        "impact": f"Impact: {task['impact']}/10",
                        "source": task["source"]
                    })
        
        # Identify time-critical tasks
        now = datetime.now()
        for task in self.tasks:
            if task.get("details", {}).get("deadline"):
                deadline = datetime.fromisoformat(task["details"]["deadline"])
                if deadline < now + timedelta(days=2):
                    self.stats["time_critical"].append({
                        "task": task["title"],
                        "deadline": task["details"]["deadline"],
                        "source": task["source"]
                    })


class MissionControl:
    """Generates mission control dashboard and action lists"""
    
    def __init__(self, scan_data: Dict[str, Any]):
        self.data = scan_data
        self.tasks = scan_data["tasks"]
        self.stats = scan_data["stats"]
    
    def generate_dashboard(self) -> str:
        """Generate ONE-PAGE mission control overview"""
        output = []
        
        output.append("=" * 80)
        output.append("🚀 MISSION CONTROL - AI EMPIRE")
        output.append("=" * 80)
        output.append(f"Scan Time: {self.data['scan_time']}")
        output.append("")
        
        # Total Overview
        output.append("📊 OVERVIEW")
        output.append("-" * 80)
        output.append(f"TOTAL OPEN TASKS: {self.stats['total_open']}")
        output.append("")
        output.append("By Category:")
        for category in CATEGORIES:
            count = self.stats['by_category'].get(category, 0)
            output.append(f"  {category:12s}: {count:3d} tasks")
        output.append("")
        
        # Top 10 Blockers
        output.append("🚨 TOP 10 BLOCKERS")
        output.append("-" * 80)
        for i, blocker in enumerate(self.stats["blockers"][:10], 1):
            output.append(f"{i:2d}. [{blocker['source']:15s}] {blocker['task']}")
            output.append(f"    Reason: {blocker['reason']}")
        if not self.stats["blockers"]:
            output.append("  ✅ No blockers detected!")
        output.append("")
        
        # Top 10 Levers
        output.append("💎 TOP 10 HIGH-IMPACT LEVERS")
        output.append("-" * 80)
        for i, lever in enumerate(self.stats["levers"][:10], 1):
            output.append(f"{i:2d}. [{lever['source']:15s}] {lever['task']}")
            output.append(f"    {lever['impact']}")
        output.append("")
        
        # Time Critical
        output.append("⏰ TIME-CRITICAL TASKS")
        output.append("-" * 80)
        if self.stats["time_critical"]:
            for task in self.stats["time_critical"]:
                output.append(f"  • {task['task']} (Deadline: {task['deadline']})")
        else:
            output.append("  ✅ No urgent deadlines!")
        output.append("")
        
        # Cost Risks
        output.append("💰 COST RISKS")
        output.append("-" * 80)
        if self.stats["cost_risks"]:
            for risk in self.stats["cost_risks"][:10]:
                risk_type = risk.get("type", "Unknown")
                risk_level = risk.get("risk", "Unknown")
                name = risk.get("service") or risk.get("task", "Unknown")
                output.append(f"  • [{risk_type:10s}] {name} - Risk: {risk_level}")
                if "tokens" in risk:
                    output.append(f"    Tokens: {risk['tokens']:,}")
        else:
            output.append("  ✅ No significant cost risks!")
        output.append("")
        
        # Compact Task Table (5 per category, max)
        output.append("📋 TASK OVERVIEW (Max 5 per category)")
        output.append("-" * 80)
        
        for category in CATEGORIES:
            category_tasks = [t for t in self.tasks if t["category"] == category][:5]
            if category_tasks:
                output.append(f"\n{category}:")
                output.append(f"{'ID':20s} {'Title':40s} {'Impact':8s} {'Urgency':8s}")
                output.append("-" * 80)
                
                for task in category_tasks:
                    task_id = task["id"][:18]
                    title = task["title"][:38]
                    impact = f"{task['impact']}/10"
                    urgency = f"{task['urgency']}/10"
                    output.append(f"{task_id:20s} {title:40s} {impact:8s} {urgency:8s}")
        
        output.append("")
        output.append("=" * 80)
        
        return "\n".join(output)
    
    def generate_next_90_min(self) -> str:
        """Generate action list for next 90 minutes (max 7 items)"""
        output = []
        
        output.append("⚡ NEXT 90 MINUTES - ACTION LIST")
        output.append("=" * 80)
        
        # Get top 7 tasks by priority score
        top_tasks = self.tasks[:7]
        
        for i, task in enumerate(top_tasks, 1):
            output.append(f"{i}. [{task['category']:10s}] {task['title']}")
            output.append(f"   Source: {task['source']} | Impact: {task['impact']}/10 | Urgency: {task['urgency']}/10")
            output.append(f"   Estimated Effort: {task['effort']}/10")
            output.append("")
        
        output.append("=" * 80)
        output.append("💡 Focus on IMPACT > URGENCY > EFFORT")
        output.append("")
        
        return "\n".join(output)
    
    def export_json(self, filepath: str = None):
        """Export detailed data to JSON for knowledge graph"""
        if filepath is None:
            filepath = f"mission_control_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            "scan_time": self.data["scan_time"],
            "summary": {
                "total_open": self.stats["total_open"],
                "by_category": dict(self.stats["by_category"]),
                "blockers_count": len(self.stats["blockers"]),
                "levers_count": len(self.stats["levers"]),
                "cost_risks_count": len(self.stats["cost_risks"])
            },
            "blockers": self.stats["blockers"],
            "levers": self.stats["levers"],
            "time_critical": self.stats["time_critical"],
            "cost_risks": self.stats["cost_risks"],
            "all_tasks": self.tasks
        }
        
        with open(filepath, "w") as f:
            json.dump(export_data, f, indent=2)
        
        return filepath


def main():
    """Main execution"""
    print("🚀 Starting Mission Control Scan...\n")
    
    # Scan all systems
    scanner = TaskScanner()
    scan_data = scanner.scan_all()
    
    print(f"\n✅ Scan complete! Found {scan_data['stats']['total_open']} tasks\n")
    
    # Generate mission control dashboard
    mc = MissionControl(scan_data)
    
    # Print dashboard
    dashboard = mc.generate_dashboard()
    print(dashboard)
    
    print("\n")
    
    # Print next 90 min action list
    action_list = mc.generate_next_90_min()
    print(action_list)
    
    # Export JSON
    json_file = mc.export_json()
    print(f"📄 Detailed data exported to: {json_file}")
    
    print("\n✨ Mission Control scan complete!")


if __name__ == "__main__":
    main()
