"""
Gemini Mirror - Configuration
Zentrale Konfiguration fuer das Gemini-Spiegel-System.
Beide Gehirne (Main Mac + Gemini Mirror) teilen sich Zustand und Vision.
"""

import os
from pathlib import Path

# === Verzeichnisse ===
MIRROR_DIR = Path(__file__).parent
STATE_DIR = MIRROR_DIR / "state"
OUTPUT_DIR = MIRROR_DIR / "output"
HISTORY_DIR = MIRROR_DIR / "history"
MEMORY_DIR = MIRROR_DIR / "memory"
PROJECT_ROOT = MIRROR_DIR.parent

# State-Dateien
MIRROR_STATE_FILE = STATE_DIR / "mirror_state.json"
VISION_STATE_FILE = STATE_DIR / "vision_state.json"
SYNC_STATE_FILE = STATE_DIR / "sync_state.json"
DUAL_BRAIN_STATE_FILE = STATE_DIR / "dual_brain_state.json"
QUESTION_LOG_FILE = STATE_DIR / "question_log.json"

# Memory-Dateien (persistentes Gedaechtnis)
VISION_MEMORY_FILE = MEMORY_DIR / "vision_memory.json"
PATTERN_CROSS_FILE = MEMORY_DIR / "cross_patterns.json"
PERSONALITY_FILE = MEMORY_DIR / "maurice_profile.json"

# === API Keys ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# === Gemini Model-Routing ===
GEMINI_MODELS = {
    "flash": "gemini-2.0-flash",
    "pro": "gemini-2.0-pro",
    "thinking": "gemini-2.0-flash-thinking",
}

# Standard-Routing pro Aufgabe
MODEL_ROUTING = {
    "audit": {"provider": "gemini", "model": "flash", "temp": 0.4},
    "architect": {"provider": "gemini", "model": "pro", "temp": 0.7},
    "analyst": {"provider": "gemini", "model": "flash", "temp": 0.5},
    "refinery": {"provider": "gemini", "model": "pro", "temp": 0.6},
    "compounder": {"provider": "gemini", "model": "pro", "temp": 0.7},
    "vision_questions": {"provider": "gemini", "model": "pro", "temp": 0.9},
    "reflection": {"provider": "gemini", "model": "thinking", "temp": 0.5},
    "sync_analysis": {"provider": "gemini", "model": "flash", "temp": 0.3},
    "cowork_plan": {"provider": "gemini", "model": "pro", "temp": 0.7},
    "cowork_act": {"provider": "gemini", "model": "flash", "temp": 0.6},
    "cowork_reflect": {"provider": "gemini", "model": "thinking", "temp": 0.5},
}

# === Gemini API Endpoints ===
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_GENERATE_URL = f"{GEMINI_BASE_URL}/models/{{model}}:generateContent"

# === Sync-Konfiguration ===
SYNC_CONFIG = {
    "interval_seconds": 900,  # Alle 15 Minuten
    "git_remote": "origin",
    "main_branch": "main",
    "mirror_branch": "gemini-mirror",
    "auto_push": True,
    "conflict_strategy": "merge_both",  # Beide Seiten behalten
    "sync_paths": [
        "gemini-mirror/state/",
        "gemini-mirror/output/",
        "gemini-mirror/memory/",
        "workflow-system/state/",
        "workflow-system/output/",
    ],
}

# === Vision Interrogator ===
VISION_CONFIG = {
    "questions_per_day": 5,
    "categories": [
        "vision",       # Langfristige Ziele, Traeume
        "strategy",     # Wie soll das Ziel erreicht werden
        "priorities",   # Was ist jetzt am wichtigsten
        "preferences",  # Wie arbeitest du am liebsten
        "blockers",     # Was hindert dich gerade
        "values",       # Was ist dir wichtig
        "lifestyle",    # Wie soll dein Leben aussehen
    ],
    "question_depth_levels": {
        "surface": "Einfache Ja/Nein oder Auswahl-Fragen",
        "medium": "Offene Fragen die 1-2 Saetze brauchen",
        "deep": "Reflektionsfragen die Nachdenken erfordern",
    },
    "max_stored_answers": 500,
}

# === Dual-Brain Amplification ===
DUAL_BRAIN_CONFIG = {
    "amplification_interval": 3600,  # Jede Stunde
    "cross_pollination_enabled": True,
    "competitive_analysis": True,
    "max_insights_per_cycle": 10,
    "improvement_threshold": 0.7,  # Mindest-Score fuer Uebernahme
    "brain_roles": {
        "main": {
            "name": "AIEmpire-Main",
            "strengths": ["execution", "kimi_swarm", "cost_efficiency"],
            "primary_model": "kimi",
        },
        "mirror": {
            "name": "AIEmpire-Gemini",
            "strengths": ["reasoning", "code_generation", "multimodal"],
            "primary_model": "gemini",
        },
    },
}

# === Resource Limits ===
RESOURCE_LIMITS = {
    "max_concurrent_gemini_calls": 10,
    "max_tokens_per_call": 8192,
    "daily_token_budget": 2_000_000,  # 2M Tokens/Tag
    "cost_per_1k_input_flash": 0.0001,
    "cost_per_1k_output_flash": 0.0004,
    "cost_per_1k_input_pro": 0.00125,
    "cost_per_1k_output_pro": 0.005,
    "emergency_stop_daily_cost": 10.0,  # Max $10/Tag
}

# === n8n Integration ===
N8N_CONFIG = {
    "base_url": os.getenv("N8N_URL", "http://localhost:5678"),
    "api_key": os.getenv("N8N_API_KEY", ""),
    "webhooks": {
        "gemini_sync": "gemini-sync",
        "vision_question": "vision-question",
        "vision_answer": "vision-answer",
        "dual_brain_pulse": "dual-brain-pulse",
    },
}

# Sicherstellen dass Verzeichnisse existieren
for d in [STATE_DIR, OUTPUT_DIR, HISTORY_DIR, MEMORY_DIR]:
    d.mkdir(parents=True, exist_ok=True)
