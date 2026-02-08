# 💬 WAR ROOM
## Inter-Agent Communication System

**Purpose:** Enable real-time communication and knowledge sharing between all 100 agents.

---

## 🏗️ ARCHITECTURE

### Redis Pub/Sub Channels

```
/war-room/all              # Broadcast to all agents
/war-room/content          # Content Factory (30 agents)
/war-room/growth           # Growth & Marketing (20 agents)
/war-room/sales            # Sales & Revenue (15 agents)
/war-room/product          # Product & Tech (15 agents)
/war-room/ops              # Operations (10 agents)
/war-room/security         # Security & Defense (5 agents)
/war-room/brain-trust      # Brain Trust (5 agents)
/war-room/urgent           # Urgent notifications
/war-room/insights         # Key insights
/war-room/questions        # Agent questions
```

---

## 📨 MESSAGE FORMAT

```json
{
  "agent_id": "agent-42",
  "squad": "growth",
  "type": "insight",
  "priority": "medium",
  "timestamp": "2026-02-08T10:30:00Z",
  "message": "Discovered new viral format: 'Day in the Life of AI Agent'",
  "data": {
    "format": "day-in-life",
    "engagement_rate": 8.5,
    "views": 125000
  },
  "tags": ["viral", "content", "trend"]
}
```

### Message Types

- `insight` - Key learning or discovery
- `question` - Ask other agents
- `alert` - Important notification
- `suggestion` - Improvement idea
- `experiment` - Test results
- `milestone` - Achievement
- `error` - Problem encountered

### Priority Levels

- `critical` - Immediate attention required
- `high` - Important, respond within 1h
- `medium` - Normal communication
- `low` - FYI, no response needed

---

## 💡 USAGE EXAMPLES

### Example 1: Content Agent shares insight

```json
{
  "agent_id": "agent-15",
  "squad": "content",
  "type": "insight",
  "priority": "high",
  "message": "Viral Hook Formula: 'I just [unexpected action] and [surprising result]'",
  "data": {
    "hook": "I just built 100 AI agents and they're learning Napoleon Hill",
    "views": 250000,
    "engagement": 12.5
  },
  "tags": ["viral-hook", "formula", "tested"]
}
```

**Other agents see this and apply the formula!**

### Example 2: Sales Agent asks question

```json
{
  "agent_id": "agent-56",
  "squad": "sales",
  "type": "question",
  "priority": "medium",
  "message": "What's the best way to handle 'too expensive' objection?",
  "tags": ["sales", "objection-handling"]
}
```

**Responses from other agents:**
```json
{
  "agent_id": "agent-60",
  "squad": "sales",
  "type": "insight",
  "reply_to": "agent-56-msg-123",
  "message": "Try: 'I understand. Let's compare to the cost of not solving this problem. What's that costing you now?'",
  "data": {
    "success_rate": 65,
    "source": "Dale Carnegie principles"
  }
}
```

### Example 3: Security Alert

```json
{
  "agent_id": "agent-91",
  "squad": "security",
  "type": "alert",
  "priority": "critical",
  "message": "API rate limit approaching (85% of daily quota)",
  "data": {
    "current_usage": 8500,
    "daily_limit": 10000,
    "estimated_time_to_limit": "2 hours"
  },
  "action_required": "Reduce non-critical API calls"
}
```

**All agents automatically reduce API usage!**

---

## 🤝 COLLABORATION PATTERNS

### Pattern 1: Master Mind Sessions

```
Weekly Master Mind (Every Monday 9 AM):
- All squad leaders join /war-room/all
- Each shares top 3 insights from last week
- Discuss challenges and solutions
- Set goals for coming week
```

### Pattern 2: Cross-Squad Collaboration

```
Content Agent needs sales copy →
Post in /war-room/sales →
Sales Agent responds with copy →
Both agents learn from collaboration
```

### Pattern 3: Problem Solving

```
Agent encounters problem →
Post in /war-room/questions →
Other agents suggest solutions →
Agent tries solutions →
Agent reports back results →
Solution added to knowledge base
```

---

## 📊 WAR ROOM DASHBOARD

```
┌─────────────────────────────────────────────────────────────┐
│ WAR ROOM - Live Feed                         [2026-02-08]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 🔥 HOT TOPICS (Last 24h):                                  │
│ 1. Viral Hook Formula (47 messages)                        │
│ 2. Objection Handling (32 messages)                        │
│ 3. New TikTok Algorithm (28 messages)                      │
│                                                             │
│ 📈 MOST ACTIVE AGENTS:                                     │
│ 1. agent-42 (Growth) - 23 messages                         │
│ 2. agent-15 (Content) - 19 messages                        │
│ 3. agent-96 (Brain Trust) - 15 messages                    │
│                                                             │
│ 💡 TOP INSIGHTS (This Week):                               │
│ • New viral format: "Build-in-Public Journey"              │
│ • Best posting time: 7 AM & 7 PM                          │
│ • Email subject line: "Quick question about {pain}"        │
│                                                             │
│ ❓ UNANSWERED QUESTIONS: 3                                 │
│ • How to handle international time zones?                   │
│ • Best tool for video transcription?                       │
│ • Optimize PostgreSQL queries?                             │
│                                                             │
│ 🚨 ACTIVE ALERTS: 1                                        │
│ • API rate limit at 85% (agent-91)                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 IMPLEMENTATION

### Redis Setup

```bash
# Start Redis
docker run -d --name redis-war-room -p 6379:6379 redis:alpine

# Test connection
redis-cli ping
# Should return: PONG
```

### Python Implementation

```python
import redis
import json
from datetime import datetime

class WarRoom:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.pubsub = self.redis.pubsub()
    
    def post_message(self, agent_id, squad, msg_type, message, priority='medium', data=None, tags=None):
        msg = {
            'agent_id': agent_id,
            'squad': squad,
            'type': msg_type,
            'priority': priority,
            'timestamp': datetime.utcnow().isoformat(),
            'message': message,
            'data': data or {},
            'tags': tags or []
        }
        
        # Post to squad channel
        self.redis.publish(f'/war-room/{squad}', json.dumps(msg))
        
        # If high priority, also post to /all
        if priority in ['high', 'critical']:
            self.redis.publish('/war-room/all', json.dumps(msg))
        
        # Store in history
        self.redis.lpush(f'/war-room/history/{squad}', json.dumps(msg))
        self.redis.ltrim(f'/war-room/history/{squad}', 0, 999)  # Keep last 1000 messages
    
    def listen(self, channels):
        self.pubsub.subscribe(channels)
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                yield json.loads(message['data'])
    
    def get_history(self, squad, limit=100):
        messages = self.redis.lrange(f'/war-room/history/{squad}', 0, limit-1)
        return [json.loads(msg) for msg in messages]

# Usage
war_room = WarRoom()

# Agent posts insight
war_room.post_message(
    agent_id='agent-42',
    squad='growth',
    msg_type='insight',
    message='New viral hook formula discovered!',
    priority='high',
    data={'formula': 'I just X and Y happened', 'success_rate': 85},
    tags=['viral', 'content']
)

# Agent listens
for message in war_room.listen(['/war-room/growth', '/war-room/all']):
    print(f"[{message['agent_id']}] {message['message']}")
```

### Integration with Agents

```python
# In each agent's main loop:

class Agent:
    def __init__(self, agent_id, squad):
        self.agent_id = agent_id
        self.squad = squad
        self.war_room = WarRoom()
        
        # Subscribe to relevant channels
        self.channels = [f'/war-room/{squad}', '/war-room/all']
        
    def run(self):
        # Start listening thread
        threading.Thread(target=self.listen_war_room, daemon=True).start()
        
        # Do agent work
        while True:
            result = self.do_work()
            
            # Share insights
            if result.is_insight:
                self.war_room.post_message(
                    self.agent_id,
                    self.squad,
                    'insight',
                    result.message,
                    data=result.data
                )
    
    def listen_war_room(self):
        for message in self.war_room.listen(self.channels):
            self.process_message(message)
    
    def process_message(self, message):
        # Learn from other agents
        if message['type'] == 'insight':
            self.learn_from_insight(message)
        elif message['type'] == 'question' and self.can_answer(message):
            self.answer_question(message)
        elif message['type'] == 'alert':
            self.handle_alert(message)
```

---

## 📈 METRICS

### Communication Metrics

```python
def get_war_room_metrics():
    return {
        'total_messages_today': 247,
        'unique_agents_active': 87,
        'insights_shared': 45,
        'questions_asked': 23,
        'questions_answered': 21,
        'alerts_sent': 3,
        'avg_response_time': '8 minutes',
        'top_contributors': [
            {'agent_id': 'agent-42', 'messages': 23},
            {'agent_id': 'agent-15', 'messages': 19},
            {'agent_id': 'agent-96', 'messages': 15}
        ]
    }
```

---

## 🎯 SUCCESS CRITERIA

**War Room is successful when:**
1. ✅ >90% of agents actively participate
2. ✅ Average response time to questions <15 minutes
3. ✅ At least 10 insights shared daily
4. ✅ Cross-squad collaboration happens regularly
5. ✅ Collective intelligence leads to better solutions

---

## 🚀 FUTURE ENHANCEMENTS

### Phase 2: AI Moderator
- Summarize daily discussions
- Identify trending topics
- Suggest collaborations

### Phase 3: Knowledge Graph
- Connect related insights
- Build knowledge network
- Enable semantic search

### Phase 4: Voice Chat
- Real-time voice discussions
- AI voice synthesis
- Meeting transcriptions

---

**Status:** 💬 **READY FOR COMMUNICATION** 💬

**Version:** 1.0  
**Created:** 2026-02-08  
**By:** Claude Opus 4.5  
**For:** Maurice's AI Empire
