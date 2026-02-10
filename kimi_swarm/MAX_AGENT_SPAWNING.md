# Max Agent Spawning Guide

## Overview

This guide explains how to configure and spawn the maximum number of agents in the Kimi Swarm system.

## System Capacities

### 100K Swarm (`swarm_100k.py`)
- **Max Agents:** 100,000
- **Max Concurrent:** 50 (configurable)
- **Budget:** $15 USD
- **Use Case:** Standard bulk tasks, lead research, content generation

### 500K Swarm (`swarm_500k.py`)
- **Max Agents:** 500,000
- **Max Concurrent:** 500 (configurable)
- **Budget:** $75 USD
- **Use Case:** Enterprise-scale tasks, revenue optimization, with Claude orchestration

## Quick Start

### 1. Environment Setup

```bash
# Required: Set Kimi/Moonshot API key
export MOONSHOT_API_KEY="your-key-here"

# Optional: Set Claude API key for 500K orchestration
export ANTHROPIC_API_KEY="your-claude-key"
```

### 2. Install Dependencies

```bash
cd kimi-swarm
pip install aiohttp pyyaml
```

### 3. Spawn Max Agents

#### Test Mode (Recommended First)
```bash
# 100K Swarm: Test with 10 tasks
python3 swarm_100k.py --test

# 500K Swarm: Test with 100 tasks  
python3 swarm_500k.py --test
```

#### Production Mode
```bash
# 100K Swarm: Run 10,000 tasks
python3 swarm_100k.py -n 10000

# 500K Swarm: Run 10,000 tasks
python3 swarm_500k.py -n 10000

# 500K Swarm: Full capacity (500K tasks - WARNING: expensive!)
python3 swarm_500k.py --full
```

## Configuration

### Adjusting Max Agents

Edit the configuration in the respective Python file or use `config.yaml`:

**For 100K Swarm:**
```python
MAX_CONCURRENT = 50     # Number of parallel workers
TOTAL_AGENTS = 100000   # Maximum capacity
BUDGET_USD = 15.0       # Auto-stop at budget limit
```

**For 500K Swarm:**
```python
MAX_CONCURRENT = 500    # Number of parallel workers  
TOTAL_AGENTS = 500000   # Maximum capacity
BUDGET_USD = 75.0       # Auto-stop at budget limit
```

### Concurrency Tuning

Higher concurrency = faster processing but higher rate limiting risk:

| MAX_CONCURRENT | Speed | Rate Limiting Risk | Recommended For |
|----------------|-------|-------------------|-----------------|
| 50 | Slow | Low | Safe default |
| 100 | Medium | Medium | Balanced |
| 200 | Fast | High | Aggressive |
| 500 | Very Fast | Very High | 500K only, careful |
| 1000 | Extreme | Extreme | Not recommended |

## Validation

Both swarm systems now include automatic validation before spawning agents:

- ✅ Checks `TOTAL_AGENTS` > 0
- ✅ Checks `MAX_CONCURRENT` > 0
- ✅ Verifies API key is set
- ✅ Validates semaphore capacity
- ✅ Ensures output directories exist
- ✅ Reports estimated time and cost

If validation fails, the system will not spawn agents.

## Capacity Reporting

At startup, you'll see a capacity report:

```
🔍 VALIDATING MAX AGENT CAPACITY
============================================================
Total Agents Capacity: 500,000
  ✅ Valid agent capacity configured
Max Concurrent Workers: 500
  ✅ Valid concurrency level
  ✅ API key configured
  ✅ Semaphore initialized correctly
  ✅ All output directories exist

Capacity Report:
  • Max Agents: 500,000
  • Concurrent Workers: 500
  • Estimated Time for Full Run: 138.9 hours
  • Estimated Cost: $75.00

✅ System validated - ready to spawn max agents!
============================================================
```

## Cost Estimation

### Per-Task Cost
- **Kimi moonshot-v1-8k:** $0.0005 per 1K tokens
- **Average task:** ~400 tokens = $0.0002 per task

### Total Costs
- **100K agents @ 100,000 tasks:** ~$20 (with buffer)
- **500K agents @ 500,000 tasks:** ~$100 (with buffer)
- **Budget limits prevent overruns**

## Rate Limiting

### Symptoms
- HTTP 429 errors
- Tasks timing out
- Slower than expected progress

### Solutions
1. **Reduce MAX_CONCURRENT:** Lower to 50-100
2. **Increase BATCH_DELAY:** Add more delay between batches
3. **Use exponential backoff:** Already built-in with retries
4. **Spread over time:** Run multiple smaller batches

## Monitoring

### Real-Time Stats

During execution, you'll see stats every 5-10 batches:

```
============================================================
500K KIMI SWARM + CLAUDE ARMY - STATS
============================================================
Completed:      5,234 / 10,000
Failed:         12
Tokens Used:    2,093,600
Cost:           $1.0468 / $75.00
Est. Revenue:   €52,340
ROI:            50.0x
Rate:           12.3 tasks/sec
Elapsed:        425.1s | ETA: 385s
Claude Checks:  5
---
high_value_lead_research    : 1,247
viral_content_idea          : 1,205
competitor_intel            : 1,298
gold_nugget_extraction      : 875
revenue_optimization        : 312
strategic_partnership       : 297
============================================================
```

### Output Files

All results are saved to subdirectories:
- `output_500k/leads/` - Lead research results
- `output_500k/content/` - Content ideas
- `output_500k/competitors/` - Competitor analysis
- `output_500k/gold_nuggets/` - Business insights
- `output_500k/revenue_operations/` - Revenue optimizations
- `output_500k/claude_insights/` - Claude orchestration insights

## Best Practices

### 1. Always Test First
```bash
# Test with small batch before running full capacity
python3 swarm_500k.py --test
```

### 2. Monitor Early
Watch the first few batches to ensure:
- No rate limiting (429 errors)
- Tasks completing successfully
- Reasonable completion time per task

### 3. Start Conservative
Begin with lower MAX_CONCURRENT and increase if stable:
```python
MAX_CONCURRENT = 50  # Start here
# If stable, increase to 100, 200, etc.
```

### 4. Budget Protection
Always set `BUDGET_USD` to prevent cost overruns:
```python
BUDGET_USD = 75.0  # System auto-stops at 95% of budget
```

### 5. Use Claude Orchestration (500K only)
For 500K swarm, Claude provides strategic optimization:
- Set `ANTHROPIC_API_KEY` for enhanced orchestration
- Falls back to rule-based if not set

## Troubleshooting

### Problem: Validation fails with "API key not set"
**Solution:** 
```bash
export MOONSHOT_API_KEY="your-key-here"
```

### Problem: Rate limiting (HTTP 429)
**Solution:** Reduce MAX_CONCURRENT or increase BATCH_DELAY

### Problem: Tasks failing with timeouts
**Solution:** Check internet connection, or increase timeout in code

### Problem: Output directories missing
**Solution:** Run script from `kimi-swarm/` directory, directories auto-create

### Problem: Budget exhausted before completion
**Solution:** Increase BUDGET_USD or reduce total tasks

## Scaling to Max Capacity

To run at absolute max capacity:

```bash
# 100K Swarm: Full 100,000 tasks
python3 swarm_100k.py -n 100000

# 500K Swarm: Full 500,000 tasks (WARNING: ~$100 cost!)
python3 swarm_500k.py --full
```

**⚠️ Warning:** Full capacity runs are expensive and take hours/days to complete.

## Integration with Docker

For Docker-based deployment, environment variables in `docker-compose.yaml`:

```yaml
environment:
  - MAX_KIMI_AGENTS=50000
  - MAX_CLAUDE_AGENTS=20
  - MOONSHOT_API_KEY=${MOONSHOT_API_KEY}
  - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

## Summary

✅ **Max agent spawning is now validated** before every run  
✅ **Capacity reporting** shows expected time and cost  
✅ **Budget protection** prevents cost overruns  
✅ **Rate limiting guidance** helps optimize concurrency  
✅ **Configuration file** makes tuning easier  

Start with test mode, validate configuration, then scale to max capacity!
