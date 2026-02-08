# 🚀 AUTOPILOT EMPIRE - Quick Start Guide

## One-Line Installation

Want to run a fully autonomous AI agent system 24/7? Use the Autopilot Empire setup!

### Installation

```bash
mkdir -p ~/autopilot-empire && cd ~/autopilot-empire && curl -o setup.sh https://raw.githubusercontent.com/mauricepfeifer-ctrl/AIEmpire-Core/main/autopilot/setup.sh && bash setup.sh
```

**OR** if you've cloned this repository:

```bash
cd autopilot
bash setup.sh
```

### What You Get

- ✅ 7 Autonomous AI Agents (Content, Sales, Code, Optimizer, Monitor, Healer, Scout)
- ✅ Local LLM with Ollama (Mixtral, Llama, Qwen, DeepSeek)
- ✅ PostgreSQL database for tracking
- ✅ Redis cache for fast operations
- ✅ Automatic revenue estimation
- ✅ 24/7 operation
- ✅ Self-healing capabilities

### System Requirements

- **OS:** macOS, Linux, or Windows with WSL2
- **RAM:** Minimum 8GB, Recommended 16GB+
- **Disk:** 50GB+ free space (for LLM models)
- **Docker:** Docker & Docker Compose installed
- **Internet:** For initial model downloads

### What Happens During Setup

1. Creates directory structure
2. Generates Docker Compose configuration
3. Creates orchestrator Python code
4. Sets up PostgreSQL with proper schema
5. Starts all containers
6. Downloads 4 LLM models (20-30 min one-time)
7. Launches autonomous agents

### After Setup

Monitor the system:

```bash
# View logs
docker-compose logs -f orchestrator

# Check container status
docker-compose ps

# Query database
docker exec -it autopilot-db psql -U autopilot -d autopilot
```

### Expected Results

- **Cycle Time:** Every 15 minutes
- **Tasks per Cycle:** 23 tasks (TikTok, Fiverr, YouTube, Twitter)
- **Estimated Daily Revenue:** €70-100
- **Estimated Monthly Revenue:** €2,000-3,000

### Full Documentation

See: [autopilot/README.md](./autopilot/README.md)

### Support

- GitHub Issues: [AIEmpire-Core Issues](https://github.com/mauricepfeifer-ctrl/AIEmpire-Core/issues)
- Documentation: [Main README](./README.md)

---

**LET'S BUILD THE AUTONOMOUS EMPIRE! 🏰💰🚀**
