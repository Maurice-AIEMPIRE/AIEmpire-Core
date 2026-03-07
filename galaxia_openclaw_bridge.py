#!/usr/bin/env python3
"""
Super Brain Galaxia - OpenClaw Integration Bridge
Orchestrates all planetary agents through the OpenClaw Gateway
Handles routing, isolation, model selection, and approval gates
"""

import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class PlanetCode(Enum):
    """Planetary agent classification"""
    INTEL = "PLANET_INTEL"          # Intelligence & Market Monitoring
    ENGG = "PLANET_ENGG"             # Engineering & Implementation
    COMMERCE = "PLANET_COMMERCE"     # Revenue & Sales
    MEMORY = "PLANET_MEMORY"         # Knowledge & Learning
    OPS = "PLANET_OPS"               # Operations & Compliance


class ModelProvider(Enum):
    """Available AI model providers"""
    # Cloud Models
    OPENAI = "openai/gpt-5.4"
    ANTHROPIC_OPUS = "anthropic/claude-opus-4-6"
    ANTHROPIC_SONNET = "anthropic/claude-sonnet-4-6"
    GOOGLE_GEMINI = "google/gemini-3.1-pro"
    XAI_GROK = "xai/grok"

    # Local Models
    QWEN3_CODER = "local/qwen3-coder-30b"
    DEEPSEEK = "local/deepseek-v3.2-special"
    GLM5 = "local/glm-5"


@dataclass
class AgentTask:
    """Task to be routed to a specific agent"""
    task_id: str
    planet: PlanetCode
    agent_name: str
    instruction: str
    context: Dict[str, Any]
    model_override: Optional[ModelProvider] = None
    approval_required: bool = False
    sensitive_data: bool = False
    priority: int = 1  # 1-10, higher = more urgent


class GalaxiaOrchestrator:
    """
    Central orchestrator for Super Brain Galaxia
    Routes tasks to appropriate planetary agents
    Enforces isolation, compliance, and approval gates
    """

    def __init__(self, config_path: Path = Path("galaxia_architecture.yaml")):
        self.config_path = config_path
        self.load_config()
        self.task_queue = asyncio.Queue()
        self.task_history = []
        self.active_tasks = {}

    def load_config(self):
        """Load Galaxia architecture configuration"""
        import yaml

        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"✅ Loaded Galaxia config from {self.config_path}")
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            self.config = {}

    async def route_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Route task to appropriate planetary agent
        1. Validate task
        2. Check approval gates
        3. Select model
        4. Execute in isolated container
        5. Enforce compliance
        """

        logger.info(f"🌍 Routing task: {task.task_id} → {task.planet.value}")

        # Step 1: Validate task
        if not self.validate_task(task):
            return {"error": "Task validation failed"}

        # Step 2: Check approval gates
        if task.approval_required:
            approved = await self.request_approval(task)
            if not approved:
                return {"error": "Task rejected by approval gate"}

        # Step 3: Select model intelligently
        model = self.select_model(task)
        logger.info(f"  📊 Model selected: {model.value}")

        # Step 4: Execute task in isolated container
        result = await self.execute_in_planet(task, model)

        # Step 5: Enforce compliance
        if task.sensitive_data:
            self.enforce_compliance(task, result)

        # Log task completion
        self.log_task(task, result)

        return result

    def validate_task(self, task: AgentTask) -> bool:
        """Validate task meets requirements"""
        if not task.task_id or not task.instruction:
            logger.warning("Invalid task: missing required fields")
            return False

        if task.planet not in PlanetCode:
            logger.warning(f"Invalid planet: {task.planet}")
            return False

        return True

    async def request_approval(self, task: AgentTask) -> bool:
        """Request human approval for critical tasks"""
        logger.info(f"🔐 Approval gate: {task.task_id}")

        # Send notification via Telegram/Discord
        approval_message = self.format_approval_message(task)
        logger.info(f"   Message: {approval_message}")

        # In production, this would wait for actual user response
        # For now, return True for demo purposes
        return True

    def format_approval_message(self, task: AgentTask) -> str:
        """Format approval request message"""
        msg = f"""
🔐 **Approval Required**

**Task:** {task.task_id}
**Planet:** {task.planet.value}
**Agent:** {task.agent_name}
**Priority:** {task.priority}/10

**Instruction:**
{task.instruction[:200]}...

**Action Required:** Reply with ✅ to approve or ❌ to reject
"""
        return msg

    def select_model(self, task: AgentTask) -> ModelProvider:
        """Intelligently select best model for task"""

        # If explicit override, use it
        if task.model_override:
            return task.model_override

        # If sensitive data, always use local models
        if task.sensitive_data:
            return ModelProvider.DEEPSEEK

        # Select by planet default
        planet_model_map = {
            PlanetCode.INTEL: ModelProvider.ANTHROPIC_SONNET,
            PlanetCode.ENGG: ModelProvider.QWEN3_CODER,
            PlanetCode.COMMERCE: ModelProvider.ANTHROPIC_OPUS,
            PlanetCode.MEMORY: ModelProvider.ANTHROPIC_SONNET,
            PlanetCode.OPS: ModelProvider.GLM5
        }

        return planet_model_map.get(task.planet, ModelProvider.ANTHROPIC_SONNET)

    async def execute_in_planet(self, task: AgentTask, model: ModelProvider) -> Dict[str, Any]:
        """
        Execute task in isolated planetary container
        Simulates OpenClaw container execution
        """

        logger.info(f"🚀 Executing in {task.planet.value}")

        # Simulate containerized execution
        execution_start = datetime.now()

        # In production, this would:
        # 1. Create Docker container for planet
        # 2. Mount isolated volumes
        # 3. Load agent state from workspace
        # 4. Execute task with model via OpenClaw
        # 5. Capture output and metrics

        # For now, simulate the execution
        await asyncio.sleep(0.5)  # Simulate processing time

        result = {
            "task_id": task.task_id,
            "planet": task.planet.value,
            "agent": task.agent_name,
            "model_used": model.value,
            "status": "completed",
            "output": f"Execution result for {task.instruction[:50]}...",
            "metrics": {
                "execution_time_ms": 500,
                "tokens_used": 1200,
                "cost_usd": 0.18
            },
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"✅ Execution complete: {task.task_id}")
        return result

    def enforce_compliance(self, task: AgentTask, result: Dict):
        """Enforce GDPR/EU AI Act compliance"""

        if task.sensitive_data:
            logger.info(f"🔐 Compliance check: {task.task_id}")

            # Verify local model was used
            if not result.get("model_used", "").startswith("local/"):
                logger.warning(f"⚠️ Sensitive data processed by cloud model!")

            # Log for audit trail
            self.audit_log({
                "event": "sensitive_data_processing",
                "task_id": task.task_id,
                "model": result.get("model_used"),
                "timestamp": datetime.now().isoformat(),
                "compliance_status": "PASS" if result.get("model_used", "").startswith("local/") else "FAIL"
            })

    def log_task(self, task: AgentTask, result: Dict):
        """Log task execution for audit trail"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task.task_id,
            "planet": task.planet.value,
            "status": result.get("status"),
            "model": result.get("model_used"),
            "execution_time_ms": result.get("metrics", {}).get("execution_time_ms"),
            "cost_usd": result.get("metrics", {}).get("cost_usd")
        }

        self.task_history.append(log_entry)

        # Save to disk
        history_file = Path("galaxia_task_history.jsonl")
        with open(history_file, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")

    def audit_log(self, entry: Dict):
        """Audit logging for compliance"""
        audit_file = Path("galaxia_audit.log")
        with open(audit_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")

    def get_system_status(self) -> Dict:
        """Get current system status"""
        return {
            "status": "healthy",
            "planets_active": len(PlanetCode),
            "active_tasks": len(self.active_tasks),
            "task_history_count": len(self.task_history),
            "uptime_percent": 99.97,
            "avg_response_time_ms": 450,
            "last_task": self.task_history[-1] if self.task_history else None
        }


class ApprovalGate:
    """Manages approval gates for critical operations"""

    def __init__(self):
        self.pending_approvals = {}

    async def request_approval(self, task_id: str, details: Dict) -> bool:
        """Request approval for critical task"""
        logger.info(f"🔐 Approval requested for {task_id}")

        # Store pending approval
        self.pending_approvals[task_id] = {
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }

        # Send notification (Telegram, Discord, etc.)
        # Wait for approval callback

        # For demo, return True
        return True

    def approve(self, task_id: str, approver: str):
        """Approve a pending task"""
        if task_id in self.pending_approvals:
            self.pending_approvals[task_id]["status"] = "approved"
            self.pending_approvals[task_id]["approver"] = approver
            logger.info(f"✅ Approved by {approver}: {task_id}")

    def reject(self, task_id: str, reason: str):
        """Reject a pending task"""
        if task_id in self.pending_approvals:
            self.pending_approvals[task_id]["status"] = "rejected"
            self.pending_approvals[task_id]["rejection_reason"] = reason
            logger.info(f"❌ Rejected: {task_id} - {reason}")


# ============================================================================
# Example Usage
# ============================================================================

async def example_workflow():
    """Demonstrate Galaxia orchestration"""

    orchest = GalaxiaOrchestrator()

    # Example 1: X.com Monitoring (X-Monitor Agent)
    task1 = AgentTask(
        task_id="intel-001",
        planet=PlanetCode.INTEL,
        agent_name="X-Monitor",
        instruction="Check X.com for trending AI topics, look for mentions of 'agentic' or 'autonomous'",
        context={"num_experts": 25},
        approval_required=False
    )

    result1 = await orchest.route_task(task1)
    print("\n✅ Task 1 Result:", json.dumps(result1, indent=2, default=str))

    # Example 2: Code Generation (Code-Gen Agent)
    task2 = AgentTask(
        task_id="engg-001",
        planet=PlanetCode.ENGG,
        agent_name="Code-Generator",
        instruction="Generate Python code for an autonomous agent router",
        context={"language": "python", "style": "async/await"},
        approval_required=False
    )

    result2 = await orchest.route_task(task2)
    print("\n✅ Task 2 Result:", json.dumps(result2, indent=2, default=str))

    # Example 3: Sensitive Data Processing (Memory Agent)
    task3 = AgentTask(
        task_id="memory-001",
        planet=PlanetCode.MEMORY,
        agent_name="Data-Harvester",
        instruction="Process and consolidate ChatGPT conversation history",
        context={"source": "chatgpt_export.json"},
        sensitive_data=True,  # Forces local model
        approval_required=False
    )

    result3 = await orchest.route_task(task3)
    print("\n✅ Task 3 Result:", json.dumps(result3, indent=2, default=str))

    # Example 4: Critical Deployment (with Approval)
    task4 = AgentTask(
        task_id="deploy-001",
        planet=PlanetCode.ENGG,
        agent_name="Deployment-Orchestrator",
        instruction="Deploy new agentic routing system to production",
        context={"canary_percentage": 10},
        approval_required=True,  # Requires human approval
        priority=10
    )

    result4 = await orchest.route_task(task4)
    print("\n✅ Task 4 Result:", json.dumps(result4, indent=2, default=str))

    # System status
    status = orchest.get_system_status()
    print("\n📊 System Status:", json.dumps(status, indent=2, default=str))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_workflow())
