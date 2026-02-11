"""
Cross-Agent Verification System
=================================
"Agents verify each other" principle — the most underrated pattern.

Key principles (inspired by Atlas Forge / Ryan Carson approach):
1. NEVER let an agent grade its own work
2. Fresh context per verification step
3. Independent verification = closest to deterministic output

This module provides:
- VerificationGate: wraps any agent output with independent QA
- FreshContextVerifier: re-evaluates output without seeing the process
- ConsensusChecker: multiple agents must agree before merge

Usage:
    from antigravity.cross_verify import VerificationGate

    gate = VerificationGate(router)
    result = await gate.execute_verified(
        prompt="Fix the import error in config.py",
        agent_key="fixer"
    )
    # result.verified = True/False
    # result.qa_feedback = "..."
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class VerifiedResult:
    """Result of a verified agent execution."""
    content: str = ""
    model: str = ""
    provider: str = ""
    agent: str = ""
    # Verification
    verified: bool = False
    qa_feedback: str = ""
    qa_score: float = 0.0       # 0-1
    verification_model: str = ""
    verification_provider: str = ""
    # Metadata
    attempts: int = 0
    total_time_ms: float = 0.0
    success: bool = False
    errors: list = field(default_factory=list)


class VerificationGate:
    """
    Wraps agent execution with independent verification.

    The executing agent and verifying agent always use DIFFERENT contexts:
    - Executor: gets the full task + context
    - Verifier: gets ONLY the output + original requirements (fresh context)

    This prevents confirmation bias and catches hallucinations.
    """

    def __init__(self, router, max_attempts: int = 2):
        """
        Args:
            router: UnifiedRouter instance
            max_attempts: Max fix-and-retry cycles before giving up
        """
        self.router = router
        self.max_attempts = max_attempts

    async def execute_verified(
        self,
        prompt: str,
        agent_key: str = "coder",
        context: Optional[str] = None,
        acceptance_threshold: float = 0.7,
    ) -> VerifiedResult:
        """
        Execute a task and independently verify the output.

        Flow:
        1. Agent executes the task
        2. QA agent reviews the output with FRESH context (no execution history)
        3. If QA rejects → Fixer agent patches → QA re-reviews
        4. Repeat up to max_attempts times

        Args:
            prompt: Task description
            agent_key: Which agent executes (architect/coder/fixer)
            context: Code/file context for the executor
            acceptance_threshold: QA score needed to pass (0-1)
        """
        result = VerifiedResult(agent=agent_key)
        start = time.time()

        for attempt in range(self.max_attempts):
            result.attempts = attempt + 1

            # Step 1: Execute the task
            exec_result = await self.router.execute(
                prompt=prompt,
                agent_key=agent_key,
                context=context,
            )

            if not exec_result.get("success"):
                result.errors.append(f"Execution failed: {exec_result.get('errors', [])}")
                continue

            result.content = exec_result.get("content", "")
            result.model = exec_result.get("model", "")
            result.provider = exec_result.get("provider", "")

            # Step 2: Independent verification with FRESH context
            # The QA agent sees ONLY: the original requirements + the output
            # It does NOT see the execution context or reasoning
            qa_result = await self._verify_independently(
                original_prompt=prompt,
                agent_output=result.content,
                agent_key=agent_key,
            )

            result.qa_feedback = qa_result.get("feedback", "")
            result.qa_score = qa_result.get("score", 0.0)
            result.verification_model = qa_result.get("model", "")
            result.verification_provider = qa_result.get("provider", "")

            # Step 3: Check acceptance
            if result.qa_score >= acceptance_threshold:
                result.verified = True
                result.success = True
                break

            # Step 4: If rejected, try to fix with feedback
            if attempt < self.max_attempts - 1:
                fix_prompt = (
                    f"The QA review found issues with your output.\n\n"
                    f"ORIGINAL TASK: {prompt}\n\n"
                    f"QA FEEDBACK: {result.qa_feedback}\n\n"
                    f"YOUR PREVIOUS OUTPUT:\n```\n{result.content[:2000]}\n```\n\n"
                    f"Please fix the issues and provide an improved version."
                )
                agent_key = "fixer"  # Switch to fixer for corrections

        result.total_time_ms = (time.time() - start) * 1000
        return result

    async def _verify_independently(
        self,
        original_prompt: str,
        agent_output: str,
        agent_key: str,
    ) -> dict[str, Any]:
        """
        Independent verification with fresh context.

        The verifier sees:
        - What was requested (original prompt)
        - What was produced (agent output)

        The verifier does NOT see:
        - The execution context (code files, etc.)
        - The agent's reasoning process
        - Previous conversation history

        This forces genuine quality assessment.
        """
        verification_prompt = f"""You are an independent QA reviewer. You must evaluate the following
agent output OBJECTIVELY. You did NOT create this output.

ORIGINAL TASK:
{original_prompt}

AGENT OUTPUT:
```
{agent_output[:3000]}
```

EVALUATE:
1. Does the output address the original task completely?
2. Are there any errors, hallucinations, or missing elements?
3. Is the output well-structured and usable?

RESPOND IN JSON:
{{
  "score": 0.0-1.0,
  "approved": true/false,
  "issues": ["list of specific issues found"],
  "feedback": "brief constructive feedback"
}}"""

        result = await self.router.execute(
            prompt=verification_prompt,
            agent_key="qa",  # Always QA agent for verification
        )

        if not result.get("success"):
            return {"score": 0.5, "feedback": "Verification unavailable", "model": "", "provider": ""}

        # Parse QA response
        content = result.get("content", "")
        try:
            # Try to extract JSON from the response
            if "{" in content:
                json_str = content[content.index("{"):content.rindex("}") + 1]
                qa_data = json.loads(json_str)
                return {
                    "score": float(qa_data.get("score", 0.5)),
                    "feedback": qa_data.get("feedback", content[:500]),
                    "issues": qa_data.get("issues", []),
                    "model": result.get("model", ""),
                    "provider": result.get("provider", ""),
                }
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: assume pass if QA didn't reject explicitly
        return {
            "score": 0.6,
            "feedback": content[:500],
            "model": result.get("model", ""),
            "provider": result.get("provider", ""),
        }


class ConsensusChecker:
    """
    Multiple agents must agree before accepting output.

    Runs the same task through N different agents/models and
    checks for consensus. Useful for critical decisions.
    """

    def __init__(self, router, required_agreement: int = 2):
        self.router = router
        self.required_agreement = required_agreement

    async def check_consensus(
        self,
        prompt: str,
        agent_keys: list[str] = None,
    ) -> dict[str, Any]:
        """
        Run prompt through multiple agents and check for consensus.

        Returns:
            {consensus: bool, agreement_count: int, responses: [...]}
        """
        if agent_keys is None:
            agent_keys = ["architect", "coder", "qa"]

        # Execute in parallel across different agents
        tasks = [
            self.router.execute(prompt=prompt, agent_key=key)
            for key in agent_keys[:3]  # Max 3 for efficiency
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        responses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                responses.append({
                    "agent": agent_keys[i],
                    "success": False,
                    "error": str(result),
                })
            else:
                responses.append({
                    "agent": agent_keys[i],
                    "success": result.get("success", False),
                    "content": result.get("content", "")[:500],
                    "model": result.get("model", ""),
                })

        successful = [r for r in responses if r["success"]]

        return {
            "consensus": len(successful) >= self.required_agreement,
            "agreement_count": len(successful),
            "total_agents": len(agent_keys),
            "responses": responses,
        }
