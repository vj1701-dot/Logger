import jwt
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from src.config import settings

class JWTHandler:
    def __init__(self):
        self.secret_key = settings.JWT_SIGNING_KEY
        self.algorithm = "HS256"
        self.ttl_minutes = settings.JWT_TTL_MIN
    
    def create_token(self, user_data: Dict) -> str:
        """Create JWT token for user"""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_data["telegram_id"]),
            "telegram_id": user_data["telegram_id"],
            "name": user_data["name"],
            "username": user_data.get("username"),
            "role": user_data["role"],
            "iat": now,
            "exp": now + timedelta(minutes=self.ttl_minutes),
            "iss": "maintenance-task-system"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={"verify_exp": True}
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def create_magic_link_token(self, telegram_id: int) -> str:
        """Create short-lived token for magic link authentication"""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(telegram_id),
            "telegram_id": telegram_id,
            "type": "magic_link",
            "iat": now,
            "exp": now + timedelta(minutes=settings.MAGIC_LINK_TTL_MIN),
            "iss": "maintenance-task-system"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_magic_link_token(self, token: str) -> Optional[int]:
        """Verify magic link token and return telegram_id"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={"verify_exp": True}
            )
            
            if payload.get("type") == "magic_link":
                return payload.get("telegram_id")
            
            return None
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

# Global instance
jwt_handler = JWTHandler()