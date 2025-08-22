import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict
from src.storage.gcs_client import GCSClient
from src.models.user import User, UserRole

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, gcs_client: GCSClient):
        self.gcs = gcs_client
    
    async def get_user(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID"""
        try:
            user_path = f"users/{telegram_id}.json"
            data = await self.gcs.read_json(user_path)
            if not data:
                return None
            
            return User.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to get user {telegram_id}: {e}")
            return None
    
    async def create_user(
        self, 
        telegram_id: int, 
        name: str, 
        username: Optional[str] = None,
        role: UserRole = UserRole.USER
    ) -> User:
        """Create new user"""
        try:
            user = User(
                telegram_id=telegram_id,
                name=name,
                username=username,
                role=role
            )
            
            user_path = f"users/{telegram_id}.json"
            await self.gcs.write_json(user_path, user.to_dict())
            
            logger.info(f"Created user {telegram_id}")
            return user
            
        except Exception as e:
            logger.error(f"Failed to create user {telegram_id}: {e}")
            raise
    
    async def update_user(self, user: User) -> bool:
        """Update user"""
        try:
            user_path = f"users/{user.telegram_id}.json"
            success = await self.gcs.write_json(user_path, user.to_dict())
            
            if success:
                logger.info(f"Updated user {user.telegram_id}")
            
            return success
        except Exception as e:
            logger.error(f"Failed to update user {user.telegram_id}: {e}")
            return False
    
    async def get_or_create_user(
        self, 
        telegram_id: int, 
        name: str, 
        username: Optional[str] = None
    ) -> User:
        """Get existing user or create new one"""
        user = await self.get_user(telegram_id)
        if user:
            # Update last seen and potentially name/username
            user.update_last_seen()
            if user.name != name:
                user.name = name
            if user.username != username:
                user.username = username
            await self.update_user(user)
            return user
        
        return await self.create_user(telegram_id, name, username)
    
    async def update_user_role(self, telegram_id: int, role: UserRole) -> bool:
        """Update user role"""
        user = await self.get_user(telegram_id)
        if not user:
            return False
        
        user.role = role
        return await self.update_user(user)
    
    async def deactivate_user(self, telegram_id: int) -> bool:
        """Deactivate user"""
        user = await self.get_user(telegram_id)
        if not user:
            return False
        
        user.active = False
        return await self.update_user(user)
    
    async def activate_user(self, telegram_id: int) -> bool:
        """Activate user"""
        user = await self.get_user(telegram_id)
        if not user:
            return False
        
        user.active = True
        return await self.update_user(user)
    
    async def get_all_users(self) -> List[User]:
        """Get all users (alias for list_all_users)"""
        return await self.list_all_users()
    
    async def list_all_users(self) -> List[User]:
        """List all users"""
        try:
            user_paths = await self.gcs.list_objects("users/")
            users = []
            
            for path in user_paths:
                if not path.endswith('.json'):
                    continue
                
                data = await self.gcs.read_json(path)
                if data:
                    try:
                        user = User.from_dict(data)
                        users.append(user)
                    except Exception as e:
                        logger.warning(f"Failed to parse user from {path}: {e}")
            
            # Sort by last seen (most recent first)
            users.sort(key=lambda u: u.last_seen_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
            return users
            
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            return []
    
    async def list_active_users(self) -> List[User]:
        """List only active users"""
        all_users = await self.list_all_users()
        return [user for user in all_users if user.active]
    
    async def list_admins(self) -> List[User]:
        """List admin users"""
        all_users = await self.list_all_users()
        return [user for user in all_users if user.is_admin() and user.active]
    
    async def is_admin(self, telegram_id: int) -> bool:
        """Check if user is admin"""
        user = await self.get_user(telegram_id)
        return user is not None and user.is_admin() and user.active
    
    async def log_admin_action(
        self, 
        admin_telegram_id: int, 
        action: str, 
        target: str, 
        details: Dict
    ):
        """Log admin action for audit trail"""
        try:
            now = datetime.now(timezone.utc)
            date_path = now.strftime("%Y/%m/%d")
            audit_path = f"audit/{date_path}/{now.strftime('%H%M%S')}_{admin_telegram_id}.jsonl"
            
            audit_entry = {
                "timestamp": now.isoformat(),
                "adminTelegramId": admin_telegram_id,
                "action": action,
                "target": target,
                "details": details
            }
            
            await self.gcs.append_jsonl(audit_path, audit_entry)
            logger.info(f"Logged admin action: {action} by {admin_telegram_id}")
            
        except Exception as e:
            logger.error(f"Failed to log admin action: {e}")
    
    async def export_users_csv(self) -> str:
        """Export users to CSV format"""
        users = await self.list_all_users()
        
        # CSV header
        csv_lines = ["telegramId,name,username,role,active,lastSeenAt,createdAt"]
        
        for user in users:
            line = f"{user.telegram_id}," \
                   f'"{user.name}",' \
                   f'"{user.username or ""}",' \
                   f"{user.role.value}," \
                   f"{user.active}," \
                   f"{user.last_seen_at.isoformat() if user.last_seen_at else ''}," \
                   f"{user.created_at.isoformat()}"
            csv_lines.append(line)
        
        return "\n".join(csv_lines)