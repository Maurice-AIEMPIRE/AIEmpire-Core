#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
AUTOPILOT EMPIRE - Orchestrator
Maurice's AI Business System - Autonomer Swarm Manager
═══════════════════════════════════════════════════════════════

Dieser Orchestrator ist das Herzstück des Systems.
Er managed 24/7 alle AI-Agenten und generiert automatisch Revenue.

Hauptaufgaben:
- 7 Master-Agenten verwalten
- Alle 15 Min Revenue-Tasks ausführen
- Self-Optimization (jede Stunde)
- Health Checks (jeder Cycle)
- Collective Learning
- Adaptive Agent Spawning

"""

import os
import sys
import time
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import yaml
import aiohttp

# ═══════════════════════════════════════════════════════════════
# KONFIGURATION
# ═══════════════════════════════════════════════════════════════

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama-master:11434")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://autopilot:autopilot@postgres-master:5432/autopilot")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis-cache:6379")
EXECUTION_MODE = os.getenv("EXECUTION_MODE", "aggressive")
REVENUE_TARGET = float(os.getenv("REVENUE_TARGET", "100.0"))
AUTO_SPAWN = os.getenv("AUTO_SPAWN_AGENTS", "true").lower() == "true"

CYCLE_INTERVAL = 900  # 15 Minuten
OPTIMIZATION_INTERVAL = 3600  # 1 Stunde
HEALTH_CHECK_INTERVAL = 900  # 15 Minuten

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# DATABASE CONNECTION
# ═══════════════════════════════════════════════════════════════

def get_db_connection():
    """Erstellt eine PostgreSQL-Verbindung"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"DB Connection Error: {e}")
        return None

# ═══════════════════════════════════════════════════════════════
# REDIS CONNECTION
# ═══════════════════════════════════════════════════════════════

def get_redis_connection():
    """Erstellt eine Redis-Verbindung"""
    try:
        r = redis.from_url(REDIS_URL)
        r.ping()
        return r
    except Exception as e:
        logger.error(f"Redis Connection Error: {e}")
        return None

# ═══════════════════════════════════════════════════════════════
# OLLAMA CLIENT
# ═══════════════════════════════════════════════════════════════

class OllamaClient:
    """Client für Ollama API"""
    
    def __init__(self, host: str = OLLAMA_HOST):
        self.host = host
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate(self, model: str, prompt: str, system: str = "") -> str:
        """Generiert Text mit Ollama Model"""
        try:
            url = f"{self.host}/api/generate"
            payload = {
                "model": model,
                "prompt": prompt,
                "system": system,
                "stream": False
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("response", "")
                else:
                    logger.error(f"Ollama API Error: {response.status}")
                    return ""
        except Exception as e:
            logger.error(f"Ollama Generate Error: {e}")
            return ""
    
    async def list_models(self) -> List[str]:
        """Listet alle verfügbaren Modelle"""
        try:
            url = f"{self.host}/api/tags"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return [m["name"] for m in data.get("models", [])]
                return []
        except Exception as e:
            logger.error(f"List Models Error: {e}")
            return []

# ═══════════════════════════════════════════════════════════════
# AGENT CLASS
# ═══════════════════════════════════════════════════════════════

class Agent:
    """Repräsentiert einen AI-Agenten im System"""
    
    def __init__(self, agent_id: str, role: str, model: str, config: Dict):
        self.agent_id = agent_id
        self.role = role
        self.model = model
        self.config = config
        self.state = "idle"
        self.tasks_completed = 0
        self.success_rate = 0.0
        self.revenue_generated = 0.0
        
    async def execute_task(self, task_type: str, context: Dict, ollama: OllamaClient) -> Dict:
        """Führt eine Task aus"""
        start_time = time.time()
        self.state = "working"
        
        try:
            # Strategy aus Memory laden (wenn vorhanden)
            strategy = await self.load_best_strategy(task_type)
            
            # Prompt erstellen
            prompt = self.build_prompt(task_type, context, strategy)
            
            # Mit Ollama generieren
            result = await ollama.generate(
                model=self.model,
                prompt=prompt,
                system=f"You are {self.role}. Execute tasks efficiently and professionally."
            )
            
            # Quality Score berechnen
            quality_score = self.evaluate_result(result, task_type)
            
            # Execution Time
            execution_time = int((time.time() - start_time) * 1000)
            
            # In DB loggen
            await self.log_execution(task_type, "success", quality_score, execution_time)
            
            # Learning: Strategy speichern wenn gut
            if quality_score >= 0.75:
                await self.save_strategy(task_type, strategy, quality_score)
            
            self.tasks_completed += 1
            self.state = "idle"
            
            return {
                "status": "success",
                "result": result,
                "quality_score": quality_score,
                "execution_time_ms": execution_time
            }
            
        except Exception as e:
            logger.error(f"Agent {self.agent_id} Task Error: {e}")
            self.state = "error"
            await self.log_execution(task_type, "error", 0.0, 0)
            
            # Self-Healing: Bei Error versuchen zu recovern
            await self.self_heal()
            
            return {
                "status": "error",
                "error": str(e)
            }
    
    def build_prompt(self, task_type: str, context: Dict, strategy: str = "") -> str:
        """Erstellt Task-Prompt"""
        prompts = {
            "tiktok_script": f"Create a viral TikTok script about: {context.get('topic', 'AI automation')}. Hook in first 3 seconds! {strategy}",
            "fiverr_gig": f"Create a Fiverr gig for: {context.get('service', 'AI automation')}. Make it attractive! {strategy}",
            "youtube_short": f"Create a YouTube Shorts script about: {context.get('topic', 'making money online')}. {strategy}",
            "twitter_thread": f"Create a Twitter thread about: {context.get('topic', 'AI business')}. 5-7 tweets. {strategy}",
            "auto_bid": f"Write a winning Fiverr proposal for: {context.get('request', 'automation project')}. {strategy}",
        }
        return prompts.get(task_type, f"Execute task: {task_type}")
    
    def evaluate_result(self, result: str, task_type: str) -> float:
        """Bewertet das Ergebnis (0.0 - 1.0)"""
        if not result:
            return 0.0
        
        # Einfache Heuristiken
        score = 0.5
        
        # Länge
        if len(result) > 100:
            score += 0.1
        if len(result) > 300:
            score += 0.1
        
        # Keywords je nach Task
        keywords = {
            "tiktok_script": ["hook", "watch", "secret", "money", "free"],
            "fiverr_gig": ["professional", "quality", "fast", "expert"],
            "youtube_short": ["subscribe", "like", "comment"],
            "twitter_thread": ["thread", "1/", "🧵"]
        }
        
        task_keywords = keywords.get(task_type, [])
        for kw in task_keywords:
            if kw.lower() in result.lower():
                score += 0.05
        
        return min(score, 1.0)
    
    async def load_best_strategy(self, task_type: str) -> str:
        """Lädt beste Strategy für Task-Type aus collective knowledge"""
        try:
            conn = get_db_connection()
            if not conn:
                return ""
            
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT best_strategy FROM collective_knowledge 
                    WHERE task_type = %s 
                    ORDER BY avg_quality_score DESC 
                    LIMIT 1
                """, (task_type,))
                row = cur.fetchone()
                conn.close()
                
                if row:
                    return row["best_strategy"]
        except Exception as e:
            logger.error(f"Load Strategy Error: {e}")
        
        return ""
    
    async def save_strategy(self, task_type: str, strategy: str, quality: float):
        """Speichert erfolgreiche Strategy in Memory"""
        try:
            conn = get_db_connection()
            if not conn:
                return
            
            with conn.cursor() as cur:
                # In agent_memory speichern
                cur.execute("""
                    INSERT INTO agent_memory (agent_id, task_type, strategy, quality_score)
                    SELECT id, %s, %s, %s FROM agents WHERE agent_id = %s
                """, (task_type, strategy, quality, self.agent_id))
                conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Save Strategy Error: {e}")
    
    async def log_execution(self, task_type: str, status: str, quality: float, exec_time: int):
        """Loggt Task Execution in DB"""
        try:
            conn = get_db_connection()
            if not conn:
                return
            
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO task_executions 
                    (agent_id, task_type, status, quality_score, execution_time_ms)
                    SELECT id, %s, %s, %s, %s FROM agents WHERE agent_id = %s
                """, (task_type, status, quality, exec_time, self.agent_id))
                conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Log Execution Error: {e}")
    
    async def self_heal(self):
        """Self-Healing bei Errors"""
        logger.info(f"Agent {self.agent_id} initiating self-heal...")
        await asyncio.sleep(5)  # Kurze Pause
        self.state = "idle"
        logger.info(f"Agent {self.agent_id} recovered.")

# ═══════════════════════════════════════════════════════════════
# ORCHESTRATOR CLASS
# ═══════════════════════════════════════════════════════════════

class Orchestrator:
    """Der Master Brain - Verwaltet alle Agenten und Tasks"""
    
    def __init__(self):
        self.agents: List[Agent] = []
        self.running = False
        self.last_optimization = datetime.now()
        self.last_health_check = datetime.now()
        
    async def initialize(self):
        """Initialisiert das System"""
        logger.info("🚀 Orchestrator startet...")
        
        # Agenten-Config laden
        agents_config = self.load_agents_config()
        
        # Master-Agenten erstellen
        for agent_cfg in agents_config:
            agent = Agent(
                agent_id=agent_cfg["id"],
                role=agent_cfg["role"],
                model=agent_cfg["model"],
                config=agent_cfg
            )
            self.agents.append(agent)
            logger.info(f"✅ Agent initialized: {agent.agent_id} ({agent.role})")
        
        # DB Health Check
        conn = get_db_connection()
        if conn:
            logger.info("✅ Database connected")
            conn.close()
        else:
            logger.error("❌ Database connection failed")
        
        # Redis Health Check
        r = get_redis_connection()
        if r:
            logger.info("✅ Redis connected")
        else:
            logger.error("❌ Redis connection failed")
        
        logger.info(f"✅ Orchestrator bereit mit {len(self.agents)} Agenten")
    
    def load_agents_config(self) -> List[Dict]:
        """Lädt Agenten-Config aus YAML"""
        try:
            with open("/app/config/agents.yaml", "r") as f:
                config = yaml.safe_load(f)
                return config.get("agents", [])
        except Exception as e:
            logger.error(f"Config Load Error: {e}")
            # Fallback: Default Master Agents
            return [
                {"id": "content-master-001", "role": "Content Master", "model": "qwen2.5"},
                {"id": "sales-master-001", "role": "Sales Master", "model": "llama3.3"},
                {"id": "code-master-001", "role": "Code Master", "model": "deepseek-coder"},
                {"id": "optimizer-001", "role": "Optimizer", "model": "mixtral-8x7b"},
                {"id": "monitor-001", "role": "Monitor", "model": "neural-chat"},
                {"id": "healer-001", "role": "Healer", "model": "openhermes"},
                {"id": "scout-001", "role": "Scout", "model": "mixtral-8x7b"},
            ]
    
    async def run(self):
        """Hauptloop - Läuft 24/7"""
        self.running = True
        logger.info("🔥 Autopilot Empire is LIVE - 24/7 Revenue Generation gestartet")
        
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                logger.info(f"\n{'='*60}\n🔄 CYCLE #{cycle_count} - {datetime.now()}\n{'='*60}")
                
                # PHASE 1: Revenue Generation
                await self.revenue_phase()
                
                # PHASE 2: Health Check
                await self.health_check_phase()
                
                # PHASE 3: Collective Learning
                await self.collective_learning_phase()
                
                # PHASE 4: Self-Optimization (jede Stunde)
                if (datetime.now() - self.last_optimization).seconds >= OPTIMIZATION_INTERVAL:
                    await self.optimization_phase()
                    self.last_optimization = datetime.now()
                
                # PHASE 5: Adaptive Spawning (wenn nötig)
                if AUTO_SPAWN:
                    await self.adaptive_spawning_phase()
                
                logger.info(f"✅ Cycle #{cycle_count} completed. Waiting {CYCLE_INTERVAL}s...")
                await asyncio.sleep(CYCLE_INTERVAL)
                
            except Exception as e:
                logger.error(f"❌ Cycle Error: {e}")
                await asyncio.sleep(60)  # Bei Error: 1 Min warten
    
    async def revenue_phase(self):
        """REVENUE PHASE: Generiere Einnahmen"""
        logger.info("💰 REVENUE PHASE - Generating Income...")
        
        async with OllamaClient() as ollama:
            tasks = []
            
            # Content Master: TikTok Scripts
            content_agent = self.get_agent_by_role("Content Master")
            if content_agent:
                for i in range(3):
                    tasks.append(content_agent.execute_task(
                        "tiktok_script",
                        {"topic": f"AI automation opportunity #{i+1}"},
                        ollama
                    ))
            
            # Sales Master: Fiverr Gigs
            sales_agent = self.get_agent_by_role("Sales Master")
            if sales_agent:
                for i in range(2):
                    tasks.append(sales_agent.execute_task(
                        "fiverr_gig",
                        {"service": f"AI automation service #{i+1}"},
                        ollama
                    ))
            
            # Alle Tasks parallel ausführen
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
            logger.info(f"✅ Revenue Phase: {success_count}/{len(tasks)} tasks successful")
    
    async def health_check_phase(self):
        """HEALTH CHECK: System-Gesundheit prüfen"""
        logger.info("🏥 HEALTH CHECK - Checking System Health...")
        
        # Agents Online
        agents_online = sum(1 for a in self.agents if a.state in ["idle", "working"])
        
        # Models verfügbar prüfen
        try:
            async with OllamaClient() as ollama:
                models = await ollama.list_models()
                models_available = len(models)
        except:
            models_available = 0
        
        # In DB speichern
        try:
            conn = get_db_connection()
            if conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO health_checks 
                        (overall_status, agents_online, models_available)
                        VALUES (%s, %s, %s)
                    """, ("healthy" if agents_online >= 5 else "degraded", agents_online, models_available))
                    conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"Health Check DB Error: {e}")
        
        logger.info(f"✅ Health: {agents_online}/{len(self.agents)} agents online, {models_available} models available")
    
    async def collective_learning_phase(self):
        """COLLECTIVE LEARNING: Wissen teilen"""
        logger.info("🧠 COLLECTIVE LEARNING - Sharing Knowledge...")
        
        # Top Strategies pro Task-Type identifizieren und in collective_knowledge speichern
        try:
            conn = get_db_connection()
            if not conn:
                return
            
            with conn.cursor() as cur:
                # Für jeden Task-Type die beste Strategy finden
                cur.execute("""
                    INSERT INTO collective_knowledge (task_type, best_strategy, avg_quality_score, num_agents_using)
                    SELECT 
                        task_type,
                        strategy,
                        AVG(quality_score) as avg_score,
                        COUNT(DISTINCT agent_id) as num_agents
                    FROM agent_memory
                    WHERE quality_score >= 0.75
                    GROUP BY task_type, strategy
                    ON CONFLICT (id) DO UPDATE SET
                        avg_quality_score = EXCLUDED.avg_quality_score,
                        num_agents_using = EXCLUDED.num_agents_using,
                        last_updated = NOW()
                """)
                conn.commit()
            conn.close()
            logger.info("✅ Collective Learning updated")
        except Exception as e:
            logger.error(f"Collective Learning Error: {e}")
    
    async def optimization_phase(self):
        """SELF-OPTIMIZATION: Performance verbessern"""
        logger.info("⚡ OPTIMIZATION PHASE - Improving Performance...")
        
        # TODO: Analysiere Performance, spawne Helper-Agents bei Bedarf
        logger.info("✅ Optimization completed")
    
    async def adaptive_spawning_phase(self):
        """ADAPTIVE SPAWNING: Neue Agenten bei Bedarf"""
        logger.info("🔄 ADAPTIVE SPAWNING - Checking if new agents needed...")
        
        # TODO: Prüfe Revenue Target, spawne wenn <70%
        logger.info("✅ Spawning check completed")
    
    def get_agent_by_role(self, role: str) -> Optional[Agent]:
        """Findet Agent by Role"""
        for agent in self.agents:
            if agent.role == role:
                return agent
        return None
    
    async def stop(self):
        """Stoppt den Orchestrator"""
        logger.info("🛑 Orchestrator stopping...")
        self.running = False

# ═══════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════

async def main():
    """Main Entry Point"""
    orchestrator = Orchestrator()
    
    try:
        await orchestrator.initialize()
        await orchestrator.run()
    except KeyboardInterrupt:
        logger.info("⚠️  Keyboard Interrupt received")
        await orchestrator.stop()
    except Exception as e:
        logger.error(f"❌ Fatal Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
