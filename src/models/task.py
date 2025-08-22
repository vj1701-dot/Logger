from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from enum import Enum
import uuid

class TaskStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    CANCELED = "canceled"
    DONE_PENDING_REVIEW = "done_pending_review"
    DONE = "done"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class MediaType(str, Enum):
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    VOICE = "voice"

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class TelegramUser:
    def __init__(self, telegram_id: int, name: str, username: Optional[str] = None):
        self.telegram_id = telegram_id
        self.name = name
        self.username = username
    
    def to_dict(self) -> Dict:
        return {
            "telegramId": self.telegram_id,
            "name": self.name,
            "username": self.username
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TelegramUser':
        return cls(
            telegram_id=data["telegramId"],
            name=data["name"],
            username=data.get("username")
        )

class MediaItem:
    def __init__(
        self, 
        type: MediaType, 
        path: str, 
        metadata: Dict[str, Any], 
        delete_after: Optional[datetime] = None
    ):
        self.type = type
        self.path = path
        self.metadata = metadata
        self.delete_after = delete_after
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type.value,
            "path": self.path,
            "metadata": self.metadata,
            "deleteAfter": self.delete_after.isoformat() if self.delete_after else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MediaItem':
        delete_after = None
        if data.get("deleteAfter"):
            delete_after = datetime.fromisoformat(data["deleteAfter"])
        
        return cls(
            type=MediaType(data["type"]),
            path=data["path"],
            metadata=data["metadata"],
            delete_after=delete_after
        )

class TaskNote:
    def __init__(
        self, 
        id: str, 
        content: str, 
        author: TelegramUser, 
        created_at: datetime,
        media: Optional[MediaItem] = None
    ):
        self.id = id
        self.content = content
        self.author = author
        self.created_at = created_at
        self.media = media
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "author": self.author.to_dict(),
            "createdAt": self.created_at.isoformat(),
            "media": self.media.to_dict() if self.media else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TaskNote':
        media = None
        if data.get("media"):
            media = MediaItem.from_dict(data["media"])
        
        return cls(
            id=data["id"],
            content=data["content"],
            author=TelegramUser.from_dict(data["author"]),
            created_at=datetime.fromisoformat(data["createdAt"]),
            media=media
        )

class StatusHistoryEntry:
    def __init__(
        self, 
        from_status: Optional[TaskStatus], 
        to_status: TaskStatus, 
        changed_by: TelegramUser, 
        changed_at: datetime,
        reason: Optional[str] = None
    ):
        self.from_status = from_status
        self.to_status = to_status
        self.changed_by = changed_by
        self.changed_at = changed_at
        self.reason = reason
    
    def to_dict(self) -> Dict:
        return {
            "fromStatus": self.from_status.value if self.from_status else None,
            "toStatus": self.to_status.value,
            "changedBy": self.changed_by.to_dict(),
            "changedAt": self.changed_at.isoformat(),
            "reason": self.reason
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StatusHistoryEntry':
        from_status = None
        if data.get("fromStatus"):
            from_status = TaskStatus(data["fromStatus"])
        
        return cls(
            from_status=from_status,
            to_status=TaskStatus(data["toStatus"]),
            changed_by=TelegramUser.from_dict(data["changedBy"]),
            changed_at=datetime.fromisoformat(data["changedAt"]),
            reason=data.get("reason")
        )

class Task:
    def __init__(
        self,
        uid: str,
        title: str,
        description: str,
        status: TaskStatus = TaskStatus.NEW,
        priority: Priority = Priority.MEDIUM,
        created_by: Optional[TelegramUser] = None,
        assignees: Optional[List[TelegramUser]] = None,
        notes: Optional[List[TaskNote]] = None,
        media: Optional[List[MediaItem]] = None,
        status_history: Optional[List[StatusHistoryEntry]] = None,
        on_hold_reason: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.uid = uid
        self.title = title
        self.description = description
        self.status = status
        self.priority = priority
        self.created_by = created_by
        self.assignees = assignees or []
        self.notes = notes or []
        self.media = media or []
        self.status_history = status_history or []
        self.on_hold_reason = on_hold_reason
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
    
    def add_note(self, content: str, author: TelegramUser, media: Optional[MediaItem] = None) -> TaskNote:
        note = TaskNote(
            id=str(uuid.uuid4()),
            content=content,
            author=author,
            created_at=datetime.now(timezone.utc),
            media=media
        )
        self.notes.append(note)
        self.updated_at = datetime.now(timezone.utc)
        return note
    
    def change_status(
        self, 
        new_status: TaskStatus, 
        changed_by: TelegramUser, 
        reason: Optional[str] = None
    ):
        if new_status == self.status:
            return
        
        history_entry = StatusHistoryEntry(
            from_status=self.status,
            to_status=new_status,
            changed_by=changed_by,
            changed_at=datetime.now(timezone.utc),
            reason=reason
        )
        
        self.status_history.append(history_entry)
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)
        
        if new_status == TaskStatus.ON_HOLD:
            self.on_hold_reason = reason
        elif self.on_hold_reason and new_status != TaskStatus.ON_HOLD:
            self.on_hold_reason = None
    
    def add_assignee(self, assignee: TelegramUser):
        if not any(a.telegram_id == assignee.telegram_id for a in self.assignees):
            self.assignees.append(assignee)
            self.updated_at = datetime.now(timezone.utc)
    
    def remove_assignee(self, telegram_id: int):
        self.assignees = [a for a in self.assignees if a.telegram_id != telegram_id]
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict:
        return {
            "uid": self.uid,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "createdBy": self.created_by.to_dict() if self.created_by else None,
            "assignees": [a.to_dict() for a in self.assignees],
            "notes": [n.to_dict() for n in self.notes],
            "media": [m.to_dict() for m in self.media],
            "statusHistory": [h.to_dict() for h in self.status_history],
            "onHoldReason": self.on_hold_reason,
            "timestamps": {
                "createdAt": self.created_at.isoformat(),
                "updatedAt": self.updated_at.isoformat()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        created_by = None
        if data.get("createdBy"):
            created_by = TelegramUser.from_dict(data["createdBy"])
        
        assignees = [TelegramUser.from_dict(a) for a in data.get("assignees", [])]
        notes = [TaskNote.from_dict(n) for n in data.get("notes", [])]
        media = [MediaItem.from_dict(m) for m in data.get("media", [])]
        status_history = [StatusHistoryEntry.from_dict(h) for h in data.get("statusHistory", [])]
        
        timestamps = data.get("timestamps", {})
        created_at = datetime.fromisoformat(timestamps.get("createdAt", datetime.now(timezone.utc).isoformat()))
        updated_at = datetime.fromisoformat(timestamps.get("updatedAt", datetime.now(timezone.utc).isoformat()))
        
        return cls(
            uid=data["uid"],
            title=data["title"],
            description=data["description"],
            status=TaskStatus(data["status"]),
            priority=Priority(data.get("priority", "medium")),
            created_by=created_by,
            assignees=assignees,
            notes=notes,
            media=media,
            status_history=status_history,
            on_hold_reason=data.get("onHoldReason"),
            created_at=created_at,
            updated_at=updated_at
        )