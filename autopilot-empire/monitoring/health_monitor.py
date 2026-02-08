#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
AUTOPILOT EMPIRE - Health Monitor
Maurice's AI Business System - 24/7 System Monitoring
═══════════════════════════════════════════════════════════════

Überwacht kontinuierlich:
- System Health (CPU, Memory)
- Agent Status
- Database Performance
- Ollama Availability
- Revenue Progress

"""

import os
import time
import psutil
import logging
from datetime import datetime
from typing import Dict
import psycopg2
from psycopg2.extras import RealDictCursor
import aiohttp
import asyncio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://autopilot:autopilot@postgres-master:5432/autopilot")
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://orchestrator:8000")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama-master:11434")
CHECK_INTERVAL = 300  # 5 Minuten

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# FastAPI App
app = FastAPI(title="Autopilot Empire Monitor", version="1.0")

# ═══════════════════════════════════════════════════════════════
# HEALTH CHECKS
# ═══════════════════════════════════════════════════════════════

async def check_database() -> Dict:
    """Check database connectivity and performance"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        start = time.time()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        latency_ms = int((time.time() - start) * 1000)
        conn.close()
        
        return {
            "status": "healthy",
            "latency_ms": latency_ms
        }
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

async def check_ollama() -> Dict:
    """Check Ollama availability"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OLLAMA_HOST}/api/tags", timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    models = [m["name"] for m in data.get("models", [])]
                    return {
                        "status": "healthy",
                        "models_available": len(models),
                        "models": models[:5]  # First 5
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status}"
                    }
    except Exception as e:
        logger.error(f"Ollama check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

async def check_agents() -> Dict:
    """Check agent status from database"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN state = 'idle' THEN 1 END) as idle,
                    COUNT(CASE WHEN state = 'working' THEN 1 END) as working,
                    COUNT(CASE WHEN state = 'error' THEN 1 END) as error
                FROM agents
            """)
            stats = cur.fetchone()
        conn.close()
        
        return {
            "status": "healthy" if stats["error"] == 0 else "degraded",
            "total": int(stats["total"]),
            "idle": int(stats["idle"]),
            "working": int(stats["working"]),
            "error": int(stats["error"])
        }
    except Exception as e:
        logger.error(f"Agents check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

async def check_system_resources() -> Dict:
    """Check system CPU and memory"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        return {
            "status": "healthy" if cpu_percent < 90 and memory.percent < 90 else "warning",
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3)
        }
    except Exception as e:
        logger.error(f"System check failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

async def get_revenue_progress() -> Dict:
    """Check today's revenue progress vs target"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    COALESCE(SUM(amount_eur), 0) as current_revenue,
                    100.0 as target_revenue
                FROM revenue_events
                WHERE DATE(recorded_at) = CURRENT_DATE
            """)
            data = cur.fetchone()
        conn.close()
        
        current = float(data["current_revenue"])
        target = float(data["target_revenue"])
        percent = (current / target * 100) if target > 0 else 0
        
        return {
            "current_eur": current,
            "target_eur": target,
            "percent_of_target": percent,
            "status": "on_track" if percent >= 70 else "behind"
        }
    except Exception as e:
        logger.error(f"Revenue check failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

# ═══════════════════════════════════════════════════════════════
# MONITORING LOOP
# ═══════════════════════════════════════════════════════════════

async def monitoring_loop():
    """Main monitoring loop"""
    logger.info("🏥 Health Monitor started")
    
    while True:
        try:
            logger.info("=" * 60)
            logger.info(f"Health Check - {datetime.now()}")
            logger.info("=" * 60)
            
            # Run all checks
            db = await check_database()
            ollama = await check_ollama()
            agents = await check_agents()
            system = await check_system_resources()
            revenue = await get_revenue_progress()
            
            # Log results
            logger.info(f"Database: {db['status']}")
            logger.info(f"Ollama: {ollama['status']} - {ollama.get('models_available', 0)} models")
            logger.info(f"Agents: {agents.get('total', 0)} total, {agents.get('error', 0)} errors")
            logger.info(f"System: CPU {system.get('cpu_percent', 0):.1f}%, Memory {system.get('memory_percent', 0):.1f}%")
            logger.info(f"Revenue: €{revenue.get('current_eur', 0):.2f} / €{revenue.get('target_eur', 100):.2f} ({revenue.get('percent_of_target', 0):.1f}%)")
            
            # Store in database
            try:
                conn = psycopg2.connect(DATABASE_URL)
                with conn.cursor() as cur:
                    overall_status = "healthy"
                    if any(c.get("status") == "unhealthy" for c in [db, ollama, agents, system]):
                        overall_status = "unhealthy"
                    elif any(c.get("status") in ["degraded", "warning"] for c in [db, ollama, agents, system]):
                        overall_status = "degraded"
                    
                    cur.execute("""
                        INSERT INTO health_checks 
                        (overall_status, memory_percent, cpu_percent, agents_online, models_available)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        overall_status,
                        system.get("memory_percent", 0),
                        system.get("cpu_percent", 0),
                        agents.get("total", 0),
                        ollama.get("models_available", 0)
                    ))
                    conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Failed to store health check: {e}")
            
            # Critical Events
            if agents.get("error", 0) > 3:
                logger.warning(f"⚠️  CRITICAL: {agents['error']} agents in error state!")
                # TODO: Trigger alert
            
            if revenue.get("percent_of_target", 0) < 50:
                logger.warning(f"⚠️  WARNING: Revenue at {revenue['percent_of_target']:.1f}% of target!")
                # TODO: Trigger optimization
            
            logger.info("✅ Health check completed\n")
            
        except Exception as e:
            logger.error(f"❌ Monitoring loop error: {e}")
        
        # Wait before next check
        await asyncio.sleep(CHECK_INTERVAL)

# ═══════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.get("/")
async def get_dashboard():
    """Monitoring Dashboard"""
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Autopilot Empire Monitor</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: #0a0a0a;
            color: #00ff88;
            padding: 20px;
            margin: 0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            border-bottom: 2px solid #00ff88;
            padding-bottom: 10px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .card {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 15px;
        }
        .card h3 {
            margin-top: 0;
            color: #00ff88;
            font-size: 14px;
        }
        .status {
            font-size: 24px;
            font-weight: bold;
            margin: 10px 0;
        }
        .status.healthy { color: #00ff88; }
        .status.warning { color: #ffaa00; }
        .status.unhealthy { color: #ff0044; }
        .metric {
            font-size: 12px;
            color: #888;
            margin: 5px 0;
        }
        .refresh {
            text-align: center;
            margin-top: 20px;
            color: #666;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏥 AUTOPILOT EMPIRE MONITOR</h1>
        <div class="grid" id="dashboard"></div>
        <div class="refresh">Auto-refresh every 30 seconds</div>
    </div>
    
    <script>
        async function loadDashboard() {
            const res = await fetch('/status');
            const data = await res.json();
            
            const dashboard = document.getElementById('dashboard');
            dashboard.innerHTML = '';
            
            // Database
            addCard('Database', data.database.status, [
                `Latency: ${data.database.latency_ms || '--'}ms`
            ]);
            
            // Ollama
            addCard('Ollama', data.ollama.status, [
                `Models: ${data.ollama.models_available || 0}`,
                `Available: ${(data.ollama.models || []).join(', ')}`
            ]);
            
            // Agents
            addCard('Agents', data.agents.status, [
                `Total: ${data.agents.total || 0}`,
                `Working: ${data.agents.working || 0}`,
                `Errors: ${data.agents.error || 0}`
            ]);
            
            // System
            addCard('System', data.system.status, [
                `CPU: ${data.system.cpu_percent || 0}%`,
                `Memory: ${data.system.memory_percent || 0}%`,
                `Available: ${(data.system.memory_available_gb || 0).toFixed(1)} GB`
            ]);
            
            // Revenue
            addCard('Revenue', data.revenue.status, [
                `Current: €${(data.revenue.current_eur || 0).toFixed(2)}`,
                `Target: €${(data.revenue.target_eur || 0).toFixed(2)}`,
                `Progress: ${(data.revenue.percent_of_target || 0).toFixed(1)}%`
            ]);
        }
        
        function addCard(title, status, metrics) {
            const dashboard = document.getElementById('dashboard');
            const card = document.createElement('div');
            card.className = 'card';
            
            let statusClass = status.includes('health') ? 'healthy' : 
                             status.includes('warning') || status.includes('degrad') ? 'warning' : 
                             'unhealthy';
            
            card.innerHTML = `
                <h3>${title}</h3>
                <div class="status ${statusClass}">${status.toUpperCase()}</div>
                ${metrics.map(m => `<div class="metric">${m}</div>`).join('')}
            `;
            dashboard.appendChild(card);
        }
        
        loadDashboard();
        setInterval(loadDashboard, 30000);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html)

@app.get("/status")
async def get_status():
    """Get all system status"""
    return {
        "database": await check_database(),
        "ollama": await check_ollama(),
        "agents": await check_agents(),
        "system": await check_system_resources(),
        "revenue": await get_revenue_progress(),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """Simple health check"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ═══════════════════════════════════════════════════════════════
# STARTUP
# ═══════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """Start monitoring loop on startup"""
    asyncio.create_task(monitoring_loop())

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9090)
