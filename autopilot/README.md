# 🚀 AUTOPILOT EMPIRE - Autonomous AI Agent System

> 24/7 Automated Content Generation & Revenue System

## 📋 Overview

The Autopilot Empire system is a fully autonomous AI agent orchestrator that runs continuously to:

- Generate content for TikTok, YouTube, Twitter
- Create and bid on Fiverr gigs
- Track revenue automatically
- Self-heal and optimize
- Scale infinitely

## 🎯 Quick Start

### One-Line Setup

```bash
cd ~/autopilot-empire && bash setup.sh
```

This will:
1. ✅ Create all necessary directories
2. ✅ Generate Docker Compose configuration
3. ✅ Create orchestrator Python code
4. ✅ Set up PostgreSQL database
5. ✅ Start all Docker containers
6. ✅ Download LLM models (Mixtral, Llama, Qwen, DeepSeek)
7. ✅ Launch the autopilot system

**Setup Time:** 20-30 minutes (one-time only)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│         AUTOPILOT ORCHESTRATOR              │
│                                             │
│  ┌───────────┐  ┌───────────┐  ┌────────┐ │
│  │  Content  │  │   Sales   │  │  Code  │ │
│  │  Master   │  │   Master  │  │ Master │ │
│  └───────────┘  └───────────┘  └────────┘ │
│                                             │
│  ┌───────────┐  ┌───────────┐  ┌────────┐ │
│  │Optimizer  │  │  Monitor  │  │ Healer │ │
│  │  Master   │  │   Master  │  │ Master │ │
│  └───────────┘  └───────────┘  └────────┘ │
│                                             │
│  ┌───────────┐                             │
│  │   Scout   │                             │
│  │  Master   │                             │
│  └───────────┘                             │
└─────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
  ┌──────────┐   ┌──────────┐   ┌──────────┐
  │  Ollama  │   │PostgreSQL│   │  Redis   │
  │   LLM    │   │    DB    │   │  Cache   │
  └──────────┘   └──────────┘   └──────────┘
```

## 🤖 Autonomous Agents

### 7 Master Agents

1. **Content Master** - Generates TikTok scripts, YouTube shorts, Twitter threads
2. **Sales Master** - Creates Fiverr gigs, bids on projects, handles outreach
3. **Code Master** - Generates code, tools, automation scripts
4. **Optimizer Master** - Optimizes performance, costs, quality
5. **Monitor Master** - Tracks system health, metrics, alerts
6. **Healer Master** - Detects and fixes issues automatically
7. **Scout Master** - Discovers new opportunities, markets, trends

Each agent:
- Runs autonomously every 15 minutes
- Has its own memory and learning
- Tracks success rate
- Self-optimizes over time

## 📦 Services

### 1. Ollama Master (Port 11434)
- Local LLM inference
- Multiple models: Mixtral-8x7b, Llama3.3-70b, Qwen-72b, DeepSeek-Coder-33b
- Zero API costs
- Unlimited usage

### 2. PostgreSQL Database (Port 5432)
- Agent states and memory
- Revenue tracking
- Task execution logs
- Historical data

### 3. Redis Cache (Port 6379)
- Fast task queuing
- Agent coordination
- Real-time state management

### 4. Orchestrator (Port 8000)
- Main control system
- Agent coordination
- Task scheduling
- Revenue calculation

## 🔧 Configuration

### Environment Variables

Edit `.env` file or set in docker-compose.yml:

```bash
# Ollama Configuration
OLLAMA_HOST=http://ollama-master:11434

# Database Configuration
DATABASE_URL=postgresql://autopilot:autopilot@postgres-master:5432/autopilot

# Agent Configuration
MAX_AGENTS=7
CYCLE_INTERVAL=900  # 15 minutes in seconds
```

### Customizing Tasks

Edit `orchestrator.py` to customize the tasks:

```python
tasks = [
    {"type": "tiktok_script", "count": 3, "goal": 30.0},
    {"type": "fiverr_gig", "count": 5, "goal": 20.0},
    {"type": "fiverr_bid", "count": 10, "goal": 30.0},
    {"type": "youtube_short", "count": 3, "goal": 10.0},
    {"type": "twitter_thread", "count": 2, "goal": 10.0},
]
```

## 📊 Monitoring

### View Live Logs

```bash
# All services
docker-compose logs -f

# Orchestrator only
docker-compose logs -f orchestrator

# Ollama only
docker-compose logs -f ollama-master
```

### Check System Status

```bash
# Container status
docker-compose ps

# Resource usage
docker stats
```

### Database Queries

```bash
# Connect to database
docker exec -it autopilot-db psql -U autopilot -d autopilot

# View agents
SELECT * FROM agents;

# View recent revenue
SELECT * FROM revenue_events ORDER BY recorded_at DESC LIMIT 10;

# View task executions
SELECT * FROM task_executions ORDER BY executed_at DESC LIMIT 10;

# Total revenue
SELECT SUM(amount_eur) as total_revenue FROM revenue_events;
```

## 💰 Revenue Tracking

The system automatically tracks estimated revenue from:

- TikTok scripts: €10/script
- Fiverr gigs: €4/gig
- Fiverr bids: €3/bid
- YouTube shorts: €3.33/short
- Twitter threads: €5/thread

### Expected Revenue

- **Day 1:** €70-100 estimated
- **Week 1:** €500-700 estimated
- **Month 1:** €2,000-3,000 estimated
- **Month 3:** €9,000+ estimated

*Note: These are estimates based on task completion. Actual revenue depends on conversions and client acquisition.*

## 🔄 Maintenance

### Update Models

```bash
# Pull latest models
docker exec autopilot-ollama ollama pull mixtral-8x7b
docker exec autopilot-ollama ollama pull llama3.3-70b
docker exec autopilot-ollama ollama pull qwen-72b
docker exec autopilot-ollama ollama pull deepseek-coder-33b
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart orchestrator only
docker-compose restart orchestrator
```

### Backup Database

```bash
# Create backup
docker exec autopilot-db pg_dump -U autopilot autopilot > backup.sql

# Restore backup
docker exec -i autopilot-db psql -U autopilot autopilot < backup.sql
```

## 🛠️ Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Ollama model download fails

```bash
# Check Ollama logs
docker-compose logs ollama-master

# Manually pull models
docker exec -it autopilot-ollama ollama pull mixtral-8x7b
```

### Database connection issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres-master

# Test connection
docker exec autopilot-db psql -U autopilot -d autopilot -c "SELECT 1"

# Restart database
docker-compose restart postgres-master
```

### Orchestrator crashes

```bash
# Check orchestrator logs
docker-compose logs orchestrator

# Restart orchestrator
docker-compose restart orchestrator

# Rebuild if needed
docker-compose build orchestrator
docker-compose up -d orchestrator
```

## 📈 Scaling

### Increase Agent Count

Edit `orchestrator.py`:

```python
# Add more agents
roles = [
    ("content_master_1", AgentRole.CONTENT_CREATOR),
    ("content_master_2", AgentRole.CONTENT_CREATOR),
    ("sales_master_1", AgentRole.SALES_MASTER),
    ("sales_master_2", AgentRole.SALES_MASTER),
    # ... add more
]
```

### Faster Cycles

Edit `orchestrator.py`:

```python
# Change from 15 minutes to 5 minutes
await asyncio.sleep(300)  # 5 minutes
```

### More Tasks

Edit `orchestrator.py`:

```python
tasks = [
    {"type": "tiktok_script", "count": 10, "goal": 100.0},
    {"type": "fiverr_gig", "count": 20, "goal": 80.0},
    # ... add more tasks
]
```

## 🔒 Security

### Change Database Password

Edit `docker-compose.yml`:

```yaml
environment:
  - POSTGRES_USER=autopilot
  - POSTGRES_PASSWORD=your_secure_password_here
  - POSTGRES_DB=autopilot
```

Also update in orchestrator environment:

```yaml
environment:
  - DATABASE_URL=postgresql://autopilot:your_secure_password_here@postgres-master:5432/autopilot
```

### Firewall Rules

```bash
# Only allow local connections
sudo ufw allow from 127.0.0.1 to any port 5432
sudo ufw allow from 127.0.0.1 to any port 6379
sudo ufw allow from 127.0.0.1 to any port 11434
```

## 📞 Support

### GitHub Issues
Open an issue at: [AIEmpire-Core Issues](https://github.com/mauricepfeifer-ctrl/AIEmpire-Core/issues)

### Documentation
See main repository README: [AIEmpire-Core](https://github.com/mauricepfeifer-ctrl/AIEmpire-Core)

## 📜 License

Part of the AI Empire Core system by Maurice Pfeifer.

---

## 🎯 Next Steps

After setup:

1. ✅ Check logs: `docker-compose logs -f orchestrator`
2. ✅ Wait for first cycle (~15 min)
3. ✅ Check revenue: Query database
4. ✅ Let it run 24/7
5. ✅ Scale as needed

**The system is now autonomous. Let it work for you! 🚀💰**
