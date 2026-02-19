# Soul Architecture v2.0

## From 17 Agents to 4 Core Souls

Based on research from @tolibear_ and peer-reviewed papers on agent design.

### The Problem

17+ agents with generic souls produced mediocre output. Google DeepMind research
shows accuracy saturates or degrades past 4 agents due to "Coordination Tax."
More agents = more coordination overhead, not more throughput.

### The Solution

**4 Core Agents** with deep, experiential souls that spawn **36+ specialists** on demand.

```
souls/
  core/                    # 4 Deep Soul Files
    architect.md           # CEO - Strategy, priorities, kill decisions
    builder.md             # CTO - Products, code, quality, shipping
    money_maker.md         # Revenue - Content, leads, pricing, sales
    operator.md            # COO - Infrastructure, processes, monitoring

  specialists/             # 36+ Pre-defined Sub-Agent Templates
    engineering.yaml       # 8 specialists (python, devops, security, etc.)
    revenue.yaml           # 8 specialists (copy, SEO, pricing, etc.)
    operations.yaml        # 9 specialists (monitoring, backup, incidents, etc.)
    research.yaml          # 7 specialists (trends, competitive, BMA, etc.)
    content.yaml           # 7 specialists (threads, video, blog, etc.)

  teams/                   # Team Configurations
    default.yaml           # The Empire Core Four team config

  soul_spawner.py          # Dynamic sub-agent selection system
  README.md                # This file
```

### Key Principles

#### 1. Soul First (Lost in the Middle)
LLMs have U-shaped attention: massive weight on first and last tokens.
The soul MUST go first in the system prompt. Every token before it dilutes performance.

#### 2. Experiential > Imperative (NAACL 2024)
Wrong: "Always check code for security issues before deploying."
Right: "I've learned through painful production incidents that security review
before deployment catches the bugs that cost real money."

The first is a rule. The second is a belief. Beliefs produce expertise.

#### 3. Anti-Patterns at 30-40% (Persona Research)
What an expert refuses is more diagnostic than what they produce.
Each soul dedicates 30-40% to specific things the agent will NEVER do.

#### 4. Values Inherit, Identity Does Not
Sub-agents get: role, standards, scope, task.
Sub-agents never get: the core agent's identity or soul.

Wrong: "You are the CTO."
Right: "You are a code security auditor. Apply these standards: [specific]."

#### 5. Max 4 Concurrent (DeepMind)
Never more than 4 agents working simultaneously on related tasks.
Coordination tax past 4 multiplies errors, not throughput.

#### 6. Soul x Skill is Multiplicative
A well-aimed soul at the right domain doesn't add performance — it multiplies it.
A miscalibrated persona actively degrades output (worse than no soul).

### Usage

```python
from souls.soul_spawner import get_spawner

spawner = get_spawner()

# See what's available
print(spawner.stats())
catalog = spawner.get_spawn_catalog()

# Spawn a specialist
agent = spawner.spawn(
    specialist_key="code_reviewer",
    task="Review the auth module for OWASP Top 10",
    business_context="BMA CRM, handles GDPR-relevant customer data",
    spawned_by="builder"
)

# Use the system prompt
result = await router.query(agent.system_prompt)

# Multi-expert debate (EMNLP 2024: +8.69% truthfulness)
agents = spawner.spawn_multi_expert(
    specialist_keys=["code_reviewer", "security_auditor", "python_developer"],
    task="Evaluate the new authentication flow",
    spawned_by="builder"
)
```

### Research References

- "Lost in the Middle" — U-shaped attention pattern in LLMs
- NAACL 2024 "Better Zero-Shot Reasoning with Role-Play Prompting" — 10-60% accuracy improvement
- EMNLP 2024 Multi-Expert Prompting — +8.69% truthfulness via expert debate
- "Persona is a Double-edged Sword" — +10% with calibrated persona, degradation with miscalibrated
- Google DeepMind — Coordination tax past 4 agents
- Drew Breunig / Srihari Sriraman — System prompt determines theoretical peak performance
