"""
Ant Protocol Configuration
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from antigravity.config import _load_dotenv

_load_dotenv()

# Redis connection (colony shared state)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("ANT_REDIS_DB", "2"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# Colony settings
COLONY_ID = os.getenv("ANT_COLONY_ID", "empire-alpha")
MAX_WORKERS = int(os.getenv("ANT_MAX_WORKERS", "50"))
HEARTBEAT_INTERVAL = int(os.getenv("ANT_HEARTBEAT_SEC", "30"))
HEARTBEAT_TIMEOUT = int(os.getenv("ANT_HEARTBEAT_TIMEOUT", "90"))
TASK_CLAIM_TTL = int(os.getenv("ANT_CLAIM_TTL", "300"))

# Pheromone settings
PHEROMONE_DECAY_SEC = int(os.getenv("ANT_PHEROMONE_DECAY", "3600"))
PHEROMONE_MAX_STRENGTH = float(os.getenv("ANT_PHEROMONE_MAX", "10.0"))
PHEROMONE_MIN_STRENGTH = float(os.getenv("ANT_PHEROMONE_MIN", "0.1"))

# LiteLLM / Model routing
LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://localhost:4000")
DEFAULT_WORKER_MODEL = os.getenv("ANT_WORKER_MODEL", "gemini-flash")
QUEEN_MODEL = os.getenv("ANT_QUEEN_MODEL", "gemini-pro")

# API
ANT_API_HOST = os.getenv("ANT_API_HOST", "0.0.0.0")
ANT_API_PORT = int(os.getenv("ANT_API_PORT", "8900"))

# Redis key prefixes
KEY_PREFIX = f"ant:{COLONY_ID}"
TASK_BOARD_KEY = f"{KEY_PREFIX}:tasks"
TASK_DATA_KEY = f"{KEY_PREFIX}:task"
WORKER_REGISTRY_KEY = f"{KEY_PREFIX}:workers"
WORKER_HEARTBEAT_KEY = f"{KEY_PREFIX}:heartbeat"
PHEROMONE_KEY = f"{KEY_PREFIX}:pheromone"
RESULT_KEY = f"{KEY_PREFIX}:results"
COLONY_STATS_KEY = f"{KEY_PREFIX}:stats"
COLONY_LOG_KEY = f"{KEY_PREFIX}:log"
