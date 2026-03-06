"""
Redis State Manager - Central state storage for all Telegram Bot instances
Enables distributed, fault-tolerant bot operations with automatic failover
"""

import redis
import json
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class StateStore:
    """
    Manages user state, conversations, and task tracking via Redis.
    Provides atomic operations and automatic expiration for old sessions.
    """

    def __init__(self):
        self.r = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
        )
        # Test connection
        try:
            self.r.ping()
            logger.info("✅ Redis connected successfully")
        except redis.ConnectionError as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise

    # ==================== USER STATE ====================

    def get_user_state(self, user_id: str) -> Dict[str, Any]:
        """Get user's current conversation state"""
        state = self.r.get(f"state:{user_id}")
        return json.loads(state) if state else {}

    def set_user_state(self, user_id: str, state: Dict[str, Any], ttl: int = 86400) -> None:
        """Set user's state with auto-expiration (default 24h)"""
        self.r.set(f"state:{user_id}", json.dumps(state), ex=ttl)

    def get_conversation(self, user_id: str) -> list:
        """Get last 20 messages from user's conversation"""
        state = self.get_user_state(user_id)
        return state.get("conversation", [])[-20:]

    def append_message(self, user_id: str, role: str, content: str) -> None:
        """Add message to user's conversation history"""
        state = self.get_user_state(user_id)
        conversation = state.get("conversation", [])
        conversation.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        state["conversation"] = conversation[-50:]  # Keep last 50 messages
        self.set_user_state(user_id, state)

    # ==================== TASK MANAGEMENT ====================

    def enqueue_task(self, queue_name: str, task: Dict[str, Any]) -> str:
        """Add task to Redis queue and return task_id"""
        task_id = f"task:{task.get('user_id')}:{datetime.utcnow().timestamp()}"
        task["task_id"] = task_id
        task["status"] = "queued"
        task["created_at"] = datetime.utcnow().isoformat()

        # Store task metadata
        self.r.hset(f"tasks", task_id, json.dumps(task))
        # Enqueue for processing
        self.r.rpush(f"queue:{queue_name}", json.dumps(task))

        logger.info(f"📋 Task enqueued: {task_id}")
        return task_id

    def dequeue_task(self, queue_name: str, timeout: int = 0) -> Optional[Dict[str, Any]]:
        """Pop task from queue (blocking)"""
        result = self.r.blpop(f"queue:{queue_name}", timeout=timeout)
        if result:
            task = json.loads(result[1])
            return task
        return None

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Check task status"""
        task_data = self.r.hget("tasks", task_id)
        return json.loads(task_data) if task_data else None

    def set_task_status(self, task_id: str, status: str, result: Optional[str] = None) -> None:
        """Update task status"""
        task = self.get_task_status(task_id)
        if task:
            task["status"] = status
            task["updated_at"] = datetime.utcnow().isoformat()
            if result:
                task["result"] = result
            self.r.hset("tasks", task_id, json.dumps(task))
            logger.info(f"✅ Task {task_id} → {status}")

    # ==================== SYSTEM MONITORING ====================

    def set_bot_heartbeat(self, bot_instance_id: str, ttl: int = 30) -> None:
        """Register bot instance as alive (heartbeat)"""
        self.r.set(f"bot:heartbeat:{bot_instance_id}", datetime.utcnow().isoformat(), ex=ttl)

    def get_active_bots(self) -> list:
        """List all active bot instances"""
        keys = self.r.keys("bot:heartbeat:*")
        return [k.replace("bot:heartbeat:", "") for k in keys]

    def set_system_metric(self, metric_name: str, value: float) -> None:
        """Record system metric (CPU, RAM, etc.)"""
        self.r.hset("system:metrics", metric_name, value)

    def get_system_metrics(self) -> Dict[str, float]:
        """Get all system metrics"""
        metrics = self.r.hgetall("system:metrics")
        return {k: float(v) for k, v in metrics.items()}

    # ==================== ERROR TRACKING ====================

    def log_error(self, bot_id: str, error_type: str, error_msg: str, traceback_str: str) -> None:
        """Log error for debugging"""
        error_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "bot_id": bot_id,
            "error_type": error_type,
            "error_msg": error_msg,
            "traceback": traceback_str
        }
        self.r.rpush("errors:log", json.dumps(error_entry))
        # Keep last 1000 errors
        self.r.ltrim("errors:log", -1000, -1)

    def get_recent_errors(self, limit: int = 50) -> list:
        """Get recent error log"""
        errors = self.r.lrange("errors:log", -limit, -1)
        return [json.loads(e) for e in errors]

    # ==================== UTILITY ====================

    def health_check(self) -> bool:
        """Check Redis connectivity"""
        try:
            self.r.ping()
            return True
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False

    def clear_expired_data(self) -> None:
        """Manual cleanup of expired sessions"""
        # Redis automatically expires keys, but we can log it
        logger.info("🧹 Expired data auto-cleaned by Redis TTL")

    def get_stats(self) -> Dict[str, Any]:
        """Get Redis usage statistics"""
        info = self.r.info()
        return {
            "memory_used": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "total_commands": info.get("total_commands_processed"),
            "active_bots": len(self.get_active_bots()),
        }
