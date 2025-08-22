from datetime import datetime, timezone
from typing import Dict, Optional
from src.models.task import UserRole

class User:
    def __init__(
        self,
        telegram_id: int,
        name: str,
        username: Optional[str] = None,
        role: UserRole = UserRole.USER,
        active: bool = True,
        last_seen_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None
    ):
        self.telegram_id = telegram_id
        self.name = name
        self.username = username
        self.role = role
        self.active = active
        self.last_seen_at = last_seen_at or datetime.now(timezone.utc)
        self.created_at = created_at or datetime.now(timezone.utc)
    
    def update_last_seen(self):
        self.last_seen_at = datetime.now(timezone.utc)
    
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
    
    def to_dict(self) -> Dict:
        return {
            "telegramId": self.telegram_id,
            "name": self.name,
            "username": self.username,
            "role": self.role.value,
            "active": self.active,
            "lastSeenAt": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "createdAt": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        last_seen_at = None
        if data.get("lastSeenAt"):
            last_seen_at = datetime.fromisoformat(data["lastSeenAt"])
        
        created_at = datetime.now(timezone.utc)
        if data.get("createdAt"):
            created_at = datetime.fromisoformat(data["createdAt"])
        
        return cls(
            telegram_id=data["telegramId"],
            name=data["name"],
            username=data.get("username"),
            role=UserRole(data.get("role", "user")),
            active=data.get("active", True),
            last_seen_at=last_seen_at,
            created_at=created_at
        )