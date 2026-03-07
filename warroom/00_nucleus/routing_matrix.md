# ROUTING MATRIX — Model Selection & Privacy Rules

> Decides which model handles which task, and what data is allowed to leave the local machine.
> Owner: Maurice Pfeifer | Updated: 2026-02-10

---

## 1. Model Tiers

| Tier | Provider | Cost | Capacity | Use Case |
|------|----------|------|----------|----------|
| LOCAL | Ollama (Llama 3, Mistral, Phi, Qwen) | 0 EUR | Mac Mini M4, always on | 80–95% of all tasks |
| CLOUD-BUDGET | Kimi K2.5 (Moonshot API) | ~0.001 EUR/call | 50K–500K agent swarms | Batch content, mass research |
| CLOUD-BUDGET | OpenRouter (Groq, etc.) | varies | Fast inference | Fallback when Ollama overloaded |
| PREMIUM | Claude Sonnet 4.5 | ~0.01–0.05 EUR/call | High reasoning | Strategy, code review, orchestration |
| PREMIUM | Claude Opus 4.5/4.6 | ~0.05–0.15 EUR/call | Highest reasoning | Critical decisions, legal analysis, architecture |

---

## 2. Routing Decision Table

### When to use LOCAL (Ollama)

Use local models by default for everything unless a specific condition below pushes the task to cloud or premium.

| Task Type | Model Suggestion | Notes |
|-----------|-----------------|-------|
| Content drafts (first pass) | Llama 3 / Mistral | Bulk generation, hooks, social posts |
| Data extraction / OCR cleanup | Phi / Qwen | Structured extraction from text |
| Tagging and entity extraction | Mistral / Llama 3 | Entity/date/keyword parsing |
| File naming and normalization | Any local | Simple rule-based transforms |
| Email sequence drafts | Llama 3 | First draft, then QA refines |
| SEO keyword research (local) | Mistral | Cluster generation from seed terms |
| Code scaffolding / boilerplate | Llama 3 / Qwen | Templates, repetitive code |
| Translation (DE↔EN) | Mistral | Good enough for internal docs |
| Summary / compression | Any local | Reducing length, extracting key points |
| Deduplication checks | Phi | Similarity comparison |

### When to use CLOUD-BUDGET (Kimi / OpenRouter)

Escalate to cloud-budget when local models hit quality or throughput limits.

| Condition | Route To | Justification |
|-----------|----------|---------------|
| Batch >50 items needing parallel generation | Kimi K2.5 swarm | Local can't parallelize at scale |
| Content needs higher coherence than Ollama delivers | Kimi K2.5 | Better long-form than small local models |
| Ollama queue depth >10 tasks | OpenRouter (Groq) | Offload to prevent local bottleneck |
| Research requiring web-scale knowledge | Kimi / OpenRouter | Local models have no internet access |
| Multi-language content (beyond DE/EN) | Kimi | Better multilingual coverage |

### When to use PREMIUM (Claude)

Premium models are expensive. Use only when the quality gap justifies the cost.

| Condition | Route To | Justification |
|-----------|----------|---------------|
| Legal analysis (case law, risk, strategy) | Claude Opus | Accuracy is non-negotiable, lives depend on precision |
| Architecture decisions (system design) | Claude Opus | Wrong architecture = weeks of rework |
| Code review (security-critical) | Claude Sonnet | Catching bugs in auth, payments, data handling |
| Orchestration logic (multi-squad coordination) | Claude Sonnet | Needs deep reasoning about dependencies |
| Final QA on export-ready legal documents | Claude Opus | Last check before it goes to counsel |
| Complex strategy (pricing, positioning, risk) | Claude Sonnet | Requires nuanced multi-factor reasoning |
| Debugging failures in agent pipelines | Claude Sonnet | Needs to trace across multiple systems |
| Writing system prompts for critical agents | Claude Opus | Prompt quality = agent quality |

### Fallback Chain

If the preferred tier is unavailable:

```
LOCAL (Ollama) → CLOUD-BUDGET (Kimi/OpenRouter) → PREMIUM (Claude Sonnet) → Claude Opus
```

Never skip tiers. Always try the cheaper option first unless the task explicitly requires premium.

---

## 3. Privacy Rules

### Classification Levels

| Level | Label | Description |
|-------|-------|-------------|
| P0 | PUBLIC | Can go anywhere (published content, public docs) |
| P1 | INTERNAL | Stay within Maurice's systems, cloud OK |
| P2 | CONFIDENTIAL | Cloud only with Maurice's explicit per-file approval |
| P3 | LOCAL-ONLY | Never leaves the Mac Mini, period |

### Data Type → Privacy Level

| Data Type | Level | Allowed Processing |
|-----------|-------|-------------------|
| Legal documents (contracts, correspondence, evidence) | **P3** | LOCAL ONLY — Ollama exclusively |
| Legal analysis outputs (timelines, claims, strategy) | **P3** | LOCAL ONLY unless Maurice explicitly approves cloud for a specific file |
| Personal data (names, addresses, financial info) | **P3** | LOCAL ONLY |
| API keys, passwords, tokens | **P3** | LOCAL ONLY — never in any output file |
| Roewer GmbH related information | **P3** | LOCAL ONLY — should not exist in this repo at all |
| Business strategy docs | **P2** | Cloud with explicit approval per document |
| Customer/lead data | **P2** | Cloud with explicit approval |
| Financial projections, revenue data | **P2** | Cloud with explicit approval |
| Marketing copy and content drafts | **P1** | Cloud OK (will be published anyway) |
| Product descriptions, landing pages | **P1** | Cloud OK |
| SEO research, keyword data | **P1** | Cloud OK |
| Code (non-security) | **P1** | Cloud OK for review |
| Published social media content | **P0** | Anywhere |
| Open-source code contributions | **P0** | Anywhere |
| Public documentation | **P0** | Anywhere |

### The Golden Rule

**Legal documents are ALWAYS processed locally unless Maurice explicitly says otherwise for a specific file.**

This means:
- L01–L10 agents default to Ollama for all processing
- If Ollama quality is insufficient for a legal task, the agent flags it as `[ESCALATE: needs premium model — awaiting Maurice approval]`
- Maurice then explicitly approves or denies cloud processing for that specific document
- Approval is per-file, not blanket — "you can use Claude for legal stuff" is not valid authorization

### Cloud Authorization Protocol

When a task requires cloud processing of P2/P3 data:

1. Agent produces output with `[NEEDS CLOUD PROCESSING]` marker
2. Agent states exactly which data would be sent and to which provider
3. Maurice reviews and explicitly approves in chat or via a signed-off config entry
4. Only then does the agent proceed with cloud processing
5. Authorization is logged in `ops/logs/CLOUD_AUTH_LOG.md`

### What Never Leaves Local

Regardless of any authorization:

- Raw legal evidence files
- Opposing party personal information
- Maurice's financial account details
- Roewer GmbH proprietary information
- Authentication credentials of any kind

---

## 4. Cost Controls

| Rule | Threshold | Action |
|------|-----------|--------|
| Monthly budget ceiling | 100 EUR | Hard stop on all non-critical cloud calls |
| Warning threshold | 80 EUR | Engineering throttles cloud to critical-only |
| Single API call ceiling | 1 EUR | Requires justification before execution |
| Kimi swarm batch ceiling | 20 EUR/run | Split into smaller batches if exceeded |
| Claude Opus per-session limit | 5 calls | After 5 calls, must justify continued use |

Cost tracking is maintained by Telemetry agent (O25) in `ops/health/TELEMETRY.md`.

---

## 5. Resource Profiles (from Resource Guard)

| Profile | When | Models Active | CPU Target |
|---------|------|--------------|------------|
| STEALTH | Night runs, background tasks | Ollama only | < 30% |
| NORMAL | Daytime active work | Ollama + Kimi | < 70% |
| BEAST | Sprint sessions, batch runs | All models | < 85% |
| EMERGENCY | Auto-triggered at CPU >95% or RAM >92% | All agents paused | Recovery |

Transitions between profiles are managed by Resource Guard (`workflow-system/resource_guard.py`) and Engineering squad.

---

## 6. Decision Flowchart

```
New task arrives
       │
       ▼
Is it legal-related?
  YES → Is the data P3 (local-only)?
         YES → Use Ollama exclusively
               Quality sufficient?
                 YES → Done
                 NO  → Flag [ESCALATE] for Maurice
         NO  → Use Ollama, escalate if needed
  NO  →
       │
       ▼
Can Ollama handle it?
  YES → Use Ollama
  NO  →
       │
       ▼
Is it a batch/volume task?
  YES → Use Kimi K2.5 swarm
  NO  →
       │
       ▼
Does it need high reasoning?
  YES → Is it critical/architecture/security?
         YES → Claude Opus (log justification)
         NO  → Claude Sonnet
  NO  → OpenRouter/Groq (cheapest fast option)
```

---

## References

- `warroom/00_nucleus/CLAUDE.md` — Squad definitions and scopes
- `warroom/00_nucleus/warroom_rules.md` — Operating constraints
- `ops/configs/ROUTER.md` — Technical router implementation
- `ops/configs/PROVIDERS.md` — Cloud provider configurations
- `ops/health/TELEMETRY.md` — Cost tracking

---

*When in doubt: run it local. Cloud is a privilege, not a default.*
