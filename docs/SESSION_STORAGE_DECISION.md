# Session Storage Decision

## Decision: In-Memory Storage with Optional Redis Upgrade

### Recommended Approach: In-Memory Dictionary (Phase 1)

**Implementation:**
- Use Python dictionary to store session data in memory
- Key: `session_id` (UUID)
- Value: Session dictionary with conversation state

**Pros:**
- Simple implementation
- Fast access (no network latency)
- No additional dependencies
- Sufficient for MVP/demo

**Cons:**
- Data lost on server restart
- Not suitable for multiple server instances
- No persistence across deployments

**Code Location:**
`backend/src/orchestrator/conversation_manager.py`

```python
# In-memory storage
_sessions: Dict[str, Dict] = {}

def create_session() -> str:
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "session_id": session_id,
        "preferences": {},
        "itinerary": None,
        "conversation_history": [],
        "clarifying_questions_count": 0,
        "created_at": datetime.now(),
        "last_accessed": datetime.now()
    }
    return session_id
```

---

### Upgrade Path: Redis (Phase 2 / Production)

**When to Upgrade:**
- Need persistence across restarts
- Multiple server instances
- Production deployment
- Need session expiration

**Implementation:**
- Use Redis for session storage
- TTL (Time To Live) for session expiration
- JSON serialization for complex objects

**Code Changes:**
```python
import redis
import json
from datetime import timedelta

redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=0,
    decode_responses=True
)

def create_session() -> str:
    session_id = str(uuid.uuid4())
    session_data = {
        "session_id": session_id,
        "preferences": {},
        "itinerary": None,
        "conversation_history": [],
        "clarifying_questions_count": 0,
        "created_at": datetime.now().isoformat(),
        "last_accessed": datetime.now().isoformat()
    }
    
    redis_client.setex(
        f"session:{session_id}",
        timedelta(minutes=settings.session_timeout_minutes),
        json.dumps(session_data)
    )
    
    return session_id
```

---

### Alternative: PostgreSQL Database

**When to Use:**
- Need full data persistence
- Need to query session data
- Need audit logs
- Complex session relationships

**Implementation:**
- SQLAlchemy models for sessions
- Store conversation history in database
- Enable querying and analytics

**Not Recommended For:**
- MVP/demo phase
- Simple deployments
- When speed is critical

---

## Recommendation

**For Implementation:**
1. **Start with In-Memory Dictionary** - Simple, fast, sufficient for development
2. **Plan for Redis Upgrade** - Design code to easily switch storage backends
3. **Abstract Storage Layer** - Create interface that can be swapped

**Storage Interface Design:**
```python
# backend/src/orchestrator/storage.py
class SessionStorage(ABC):
    @abstractmethod
    def create_session(self) -> str:
        pass
    
    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Dict]:
        pass
    
    @abstractmethod
    def update_session(self, session_id: str, data: Dict):
        pass
    
    @abstractmethod
    def delete_session(self, session_id: str):
        pass

# InMemoryStorage implements SessionStorage
# RedisStorage implements SessionStorage
```

This allows easy switching between storage backends.

---

## Session Data Structure

```python
{
    "session_id": "uuid-string",
    "preferences": {
        "city": "Jaipur",
        "duration_days": 3,
        "interests": ["food", "culture"],
        "pace": "relaxed",
        "budget": "moderate"
    },
    "itinerary": {
        # Itinerary object
    },
    "conversation_history": [
        {"role": "user", "content": "...", "timestamp": "..."},
        {"role": "assistant", "content": "...", "timestamp": "..."}
    ],
    "clarifying_questions_count": 2,
    "created_at": "2024-01-15T10:00:00Z",
    "last_accessed": "2024-01-15T10:30:00Z"
}
```

---

## Session Timeout

**Default:** 60 minutes of inactivity

**Implementation:**
- Track `last_accessed` timestamp
- Clean up expired sessions periodically
- For Redis: Use TTL
- For In-Memory: Periodic cleanup task

```python
def cleanup_expired_sessions():
    """Remove sessions older than timeout."""
    current_time = datetime.now()
    expired = []
    
    for session_id, session_data in _sessions.items():
        last_accessed = session_data.get("last_accessed")
        if last_accessed and (current_time - last_accessed).total_seconds() > settings.session_timeout_minutes * 60:
            expired.append(session_id)
    
    for session_id in expired:
        del _sessions[session_id]
```
