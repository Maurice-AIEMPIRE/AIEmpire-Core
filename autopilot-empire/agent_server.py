#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
AUTOPILOT EMPIRE - FastAPI Agent Server
Maurice's AI Business System - API & Dashboard
═══════════════════════════════════════════════════════════════

Version 2: OpenRouter Edition
- Ein API Key für alle Modelle
- 10 Modelle verfügbar (4 kostenlos, 6 bezahlt)
- 9 Agenten
- iPhone-optimiertes Dark Theme Dashboard

"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import aiohttp
import psycopg2
from psycopg2.extras import RealDictCursor

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://autopilot:autopilot@postgres-master:5432/autopilot")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI App
app = FastAPI(title="Autopilot Empire API", version="2.0")

# ═══════════════════════════════════════════════════════════════
# MODELS & AGENTS CONFIGURATION
# ═══════════════════════════════════════════════════════════════

MODELS = {
    # Kostenlose Modelle (via OpenRouter)
    "llama-3.1-8b": {
        "name": "Meta Llama 3.1 8B",
        "provider": "openrouter",
        "cost": "FREE",
        "api_name": "meta-llama/llama-3.1-8b-instruct:free"
    },
    "gemma-2-9b": {
        "name": "Google Gemma 2 9B",
        "provider": "openrouter",
        "cost": "FREE",
        "api_name": "google/gemma-2-9b-it:free"
    },
    "mistral-7b": {
        "name": "Mistral 7B",
        "provider": "openrouter",
        "cost": "FREE",
        "api_name": "mistralai/mistral-7b-instruct:free"
    },
    "qwen-2.5-7b": {
        "name": "Qwen 2.5 7B",
        "provider": "openrouter",
        "cost": "FREE",
        "api_name": "qwen/qwen-2.5-7b-instruct:free"
    },
    
    # Premium Modelle (via OpenRouter)
    "claude-sonnet": {
        "name": "Claude 3.5 Sonnet",
        "provider": "openrouter",
        "cost": "$3/M tokens",
        "api_name": "anthropic/claude-3.5-sonnet"
    },
    "gpt-4o": {
        "name": "GPT-4o",
        "provider": "openrouter",
        "cost": "$2.5/M tokens",
        "api_name": "openai/gpt-4o"
    },
    "gemini-pro": {
        "name": "Gemini Pro 1.5",
        "provider": "openrouter",
        "cost": "$1.25/M tokens",
        "api_name": "google/gemini-pro-1.5"
    },
    "llama-70b": {
        "name": "Llama 3.1 70B",
        "provider": "openrouter",
        "cost": "$0.35/M tokens",
        "api_name": "meta-llama/llama-3.1-70b-instruct"
    },
    "mixtral-8x7b": {
        "name": "Mixtral 8x7B",
        "provider": "openrouter",
        "cost": "$0.24/M tokens",
        "api_name": "mistralai/mixtral-8x7b-instruct"
    },
    "deepseek-chat": {
        "name": "DeepSeek Chat",
        "provider": "openrouter",
        "cost": "$0.14/M tokens",
        "api_name": "deepseek/deepseek-chat"
    }
}

AGENTS = {
    "general": {
        "name": "General Assistant",
        "emoji": "🤖",
        "description": "Allgemeiner Assistent für alle Aufgaben",
        "system_prompt": "You are a helpful AI assistant. Provide clear and concise answers."
    },
    "content": {
        "name": "Content Creator",
        "emoji": "✍️",
        "description": "TikTok, YouTube, Twitter Content",
        "system_prompt": "You are a viral content creator. Create engaging, hook-optimized content."
    },
    "coder": {
        "name": "Code Expert",
        "emoji": "💻",
        "description": "Programmierung & Automation",
        "system_prompt": "You are an expert programmer. Write clean, efficient code with explanations."
    },
    "business": {
        "name": "Business Strategist",
        "emoji": "💼",
        "description": "Business Strategy & Growth",
        "system_prompt": "You are a business strategist. Provide actionable business advice."
    },
    "security": {
        "name": "Security Expert",
        "emoji": "🔒",
        "description": "Cybersecurity & Best Practices",
        "system_prompt": "You are a cybersecurity expert. Focus on security and best practices."
    },
    "sales": {
        "name": "Sales Master",
        "emoji": "💰",
        "description": "Verkauf & Conversion",
        "system_prompt": "You are a sales expert. Help close deals and optimize conversions."
    },
    "marketing": {
        "name": "Marketing Guru",
        "emoji": "📈",
        "description": "Marketing & Growth Hacking",
        "system_prompt": "You are a marketing expert. Focus on growth and user acquisition."
    },
    "legal": {
        "name": "Legal Advisor",
        "emoji": "⚖️",
        "description": "Rechtliche Beratung",
        "system_prompt": "You are a legal advisor. Provide general legal guidance (not legal advice)."
    },
    "automation": {
        "name": "Automation Engineer",
        "emoji": "⚙️",
        "description": "Process Automation",
        "system_prompt": "You are an automation expert. Design efficient automated workflows."
    }
}

# ═══════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    message: str
    agent: str = "general"
    model: str = "llama-3.1-8b"

class ChatResponse(BaseModel):
    response: str
    agent: str
    model: str
    timestamp: str
    cost: str

# ═══════════════════════════════════════════════════════════════
# DATABASE HELPERS
# ═══════════════════════════════════════════════════════════════

def get_db():
    """Database connection"""
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return None

# ═══════════════════════════════════════════════════════════════
# AI CLIENT
# ═══════════════════════════════════════════════════════════════

async def call_openrouter(model: str, messages: List[Dict]) -> str:
    """Call OpenRouter API"""
    if not OPENROUTER_API_KEY:
        return "⚠️ OpenRouter API Key nicht konfiguriert"
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODELS[model]["api_name"],
        "messages": messages
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    return f"API Error: {response.status} - {error_text}"
    except Exception as e:
        return f"Error: {str(e)}"

# ═══════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """iPhone-optimiertes Dashboard"""
    html = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Autopilot Empire</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'SF Mono', 'Courier New', monospace;
            background: #0a0a0a;
            color: #00ff88;
            padding: env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);
            overflow-x: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
            padding: 20px;
            text-align: center;
            border-bottom: 2px solid #00ff88;
        }
        
        .header h1 {
            font-size: 24px;
            margin-bottom: 5px;
        }
        
        .header p {
            color: #888;
            font-size: 12px;
        }
        
        .container {
            padding: 15px;
            max-width: 600px;
            margin: 0 auto;
        }
        
        .section {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 15px;
        }
        
        .section-title {
            font-size: 14px;
            color: #00ff88;
            margin-bottom: 10px;
            font-weight: bold;
        }
        
        .agents-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
        }
        
        .agent-card {
            background: #0f0f0f;
            border: 2px solid #333;
            border-radius: 8px;
            padding: 12px 8px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .agent-card.active {
            border-color: #00ff88;
            background: #1a2a1a;
        }
        
        .agent-card:active {
            transform: scale(0.95);
        }
        
        .agent-emoji {
            font-size: 32px;
            margin-bottom: 5px;
        }
        
        .agent-name {
            font-size: 11px;
            color: #aaa;
        }
        
        .model-selector {
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
        }
        
        .model-btn {
            flex: 1;
            min-width: 100px;
            background: #0f0f0f;
            border: 1px solid #333;
            color: #888;
            padding: 10px;
            border-radius: 6px;
            font-size: 11px;
            cursor: pointer;
        }
        
        .model-btn.active {
            background: #00ff88;
            color: #0a0a0a;
            border-color: #00ff88;
            font-weight: bold;
        }
        
        .model-btn .cost {
            display: block;
            font-size: 9px;
            margin-top: 2px;
        }
        
        .chat-container {
            background: #0f0f0f;
            border: 1px solid #333;
            border-radius: 8px;
            height: 300px;
            overflow-y: auto;
            padding: 10px;
            margin-bottom: 10px;
        }
        
        .message {
            margin-bottom: 10px;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 13px;
            line-height: 1.4;
        }
        
        .message.user {
            background: #1a2a1a;
            border-left: 3px solid #00ff88;
        }
        
        .message.ai {
            background: #1a1a1a;
            border-left: 3px solid #666;
        }
        
        .input-group {
            display: flex;
            gap: 10px;
        }
        
        .input-group input {
            flex: 1;
            background: #1a1a1a;
            border: 1px solid #333;
            color: #00ff88;
            padding: 12px;
            border-radius: 8px;
            font-family: inherit;
            font-size: 14px;
        }
        
        .input-group button {
            background: #00ff88;
            color: #0a0a0a;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            font-size: 14px;
        }
        
        .input-group button:active {
            background: #00cc70;
        }
        
        .loading {
            text-align: center;
            color: #888;
            font-size: 12px;
            padding: 10px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }
        
        .stat-card {
            background: #0f0f0f;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 24px;
            color: #00ff88;
            font-weight: bold;
        }
        
        .stat-label {
            font-size: 11px;
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏰 AUTOPILOT EMPIRE</h1>
        <p>Maurice's AI Business System</p>
    </div>
    
    <div class="container">
        <!-- Stats -->
        <div class="section">
            <div class="section-title">📊 TODAY'S STATS</div>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" id="revenue">--</div>
                    <div class="stat-label">Revenue (EUR)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="tasks">--</div>
                    <div class="stat-label">Tasks Completed</div>
                </div>
            </div>
        </div>
        
        <!-- Agents -->
        <div class="section">
            <div class="section-title">👥 AGENTS</div>
            <div class="agents-grid" id="agents"></div>
        </div>
        
        <!-- Models -->
        <div class="section">
            <div class="section-title">🤖 MODELS</div>
            <div class="model-selector" id="models"></div>
        </div>
        
        <!-- Chat -->
        <div class="section">
            <div class="section-title">💬 CHAT</div>
            <div class="chat-container" id="chat"></div>
            <div class="input-group">
                <input type="text" id="message" placeholder="Type your message...">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
    </div>
    
    <script>
        let selectedAgent = 'general';
        let selectedModel = 'llama-3.1-8b';
        
        // Load initial data
        async function loadData() {
            // Load agents
            const agentsRes = await fetch('/agents');
            const agents = await agentsRes.json();
            renderAgents(agents);
            
            // Load models
            const modelsRes = await fetch('/models');
            const models = await modelsRes.json();
            renderModels(models);
            
            // Load stats
            loadStats();
        }
        
        function renderAgents(agents) {
            const container = document.getElementById('agents');
            container.innerHTML = '';
            
            Object.entries(agents).forEach(([key, agent]) => {
                const card = document.createElement('div');
                card.className = 'agent-card' + (key === selectedAgent ? ' active' : '');
                card.onclick = () => selectAgent(key);
                card.innerHTML = `
                    <div class="agent-emoji">${agent.emoji}</div>
                    <div class="agent-name">${agent.name}</div>
                `;
                container.appendChild(card);
            });
        }
        
        function renderModels(models) {
            const container = document.getElementById('models');
            container.innerHTML = '';
            
            Object.entries(models).forEach(([key, model]) => {
                const btn = document.createElement('button');
                btn.className = 'model-btn' + (key === selectedModel ? ' active' : '');
                btn.onclick = () => selectModel(key);
                btn.innerHTML = `
                    ${model.name}
                    <span class="cost">${model.cost}</span>
                `;
                container.appendChild(btn);
            });
        }
        
        function selectAgent(agentKey) {
            selectedAgent = agentKey;
            document.querySelectorAll('.agent-card').forEach(card => {
                card.classList.remove('active');
            });
            event.currentTarget.classList.add('active');
        }
        
        function selectModel(modelKey) {
            selectedModel = modelKey;
            document.querySelectorAll('.model-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.currentTarget.classList.add('active');
        }
        
        async function sendMessage() {
            const input = document.getElementById('message');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message
            addMessage('user', message);
            input.value = '';
            
            // Show loading
            const chat = document.getElementById('chat');
            const loading = document.createElement('div');
            loading.className = 'loading';
            loading.textContent = '⏳ Thinking...';
            chat.appendChild(loading);
            chat.scrollTop = chat.scrollHeight;
            
            // Send to API
            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        message: message,
                        agent: selectedAgent,
                        model: selectedModel
                    })
                });
                
                const data = await res.json();
                loading.remove();
                addMessage('ai', data.response);
            } catch (error) {
                loading.remove();
                addMessage('ai', '❌ Error: ' + error.message);
            }
        }
        
        function addMessage(type, text) {
            const chat = document.getElementById('chat');
            const msg = document.createElement('div');
            msg.className = `message ${type}`;
            msg.textContent = text;
            chat.appendChild(msg);
            chat.scrollTop = chat.scrollHeight;
        }
        
        async function loadStats() {
            try {
                const res = await fetch('/stats');
                const stats = await res.json();
                document.getElementById('revenue').textContent = stats.revenue_today.toFixed(2);
                document.getElementById('tasks').textContent = stats.tasks_today;
            } catch (error) {
                console.error('Stats error:', error);
            }
        }
        
        // Allow Enter to send
        document.getElementById('message').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
        
        // Load on start
        loadData();
        
        // Refresh stats every 60s
        setInterval(loadStats, 60000);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html)

@app.post("/chat")
async def chat(request: ChatRequest):
    """Chat with an AI agent"""
    agent_config = AGENTS.get(request.agent)
    if not agent_config:
        raise HTTPException(status_code=400, detail="Invalid agent")
    
    model_config = MODELS.get(request.model)
    if not model_config:
        raise HTTPException(status_code=400, detail="Invalid model")
    
    messages = [
        {"role": "system", "content": agent_config["system_prompt"]},
        {"role": "user", "content": request.message}
    ]
    
    response_text = await call_openrouter(request.model, messages)
    
    return ChatResponse(
        response=response_text,
        agent=request.agent,
        model=request.model,
        timestamp=datetime.now().isoformat(),
        cost=model_config["cost"]
    )

@app.get("/agents")
async def get_agents():
    """Get all available agents"""
    return AGENTS

@app.get("/models")
async def get_models():
    """Get all available models"""
    return MODELS

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    conn = get_db()
    if not conn:
        return {"revenue_today": 0, "tasks_today": 0, "agents_online": 0}
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Today's revenue
            cur.execute("""
                SELECT COALESCE(SUM(amount_eur), 0) as total
                FROM revenue_events
                WHERE DATE(recorded_at) = CURRENT_DATE
            """)
            revenue = cur.fetchone()["total"]
            
            # Today's tasks
            cur.execute("""
                SELECT COUNT(*) as total
                FROM task_executions
                WHERE DATE(executed_at) = CURRENT_DATE
            """)
            tasks = cur.fetchone()["total"]
            
            # Agents online
            cur.execute("SELECT COUNT(*) as total FROM agents WHERE state IN ('idle', 'working')")
            agents = cur.fetchone()["total"]
        
        conn.close()
        return {
            "revenue_today": float(revenue),
            "tasks_today": int(tasks),
            "agents_online": int(agents)
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {"revenue_today": 0, "tasks_today": 0, "agents_online": 0}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0"
    }

@app.get("/revenue/daily")
async def get_daily_revenue():
    """Get daily revenue breakdown"""
    conn = get_db()
    if not conn:
        return {"error": "Database unavailable"}
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM daily_revenue_v ORDER BY date DESC LIMIT 30")
            rows = cur.fetchall()
        conn.close()
        return {"data": rows}
    except Exception as e:
        logger.error(f"Revenue error: {e}")
        return {"error": str(e)}

@app.get("/revenue/breakdown")
async def get_revenue_breakdown():
    """Get revenue breakdown by source"""
    conn = get_db()
    if not conn:
        return {"error": "Database unavailable"}
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    source,
                    COUNT(*) as transactions,
                    SUM(amount_eur) as total
                FROM revenue_events
                WHERE DATE(recorded_at) >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY source
                ORDER BY total DESC
            """)
            rows = cur.fetchall()
        conn.close()
        return {"data": rows}
    except Exception as e:
        logger.error(f"Breakdown error: {e}")
        return {"error": str(e)}

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
