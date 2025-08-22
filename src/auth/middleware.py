import base64
import logging
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from src.auth.jwt_handler import jwt_handler
from src.config import settings

logger = logging.getLogger(__name__)

# Routes that don't require authentication
PUBLIC_ROUTES = {
    "/",
    "/dashboard",
    "/health",
    "/webhook/telegram",
    "/api/auth/login",
    "/api/auth/magic-link",
    "/cron/media-retention"
}

# Routes that start with these prefixes are public
PUBLIC_PREFIXES = [
    "/static/",
    "/dashboard/",
    "/_next/",
    "/docs",
    "/openapi.json"
]

def is_public_route(path: str) -> bool:
    """Check if route is public"""
    if path in PUBLIC_ROUTES:
        return True
    
    return any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)

def extract_bearer_token(authorization: str) -> Optional[str]:
    """Extract Bearer token from Authorization header"""
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() == "bearer":
            return token
    except ValueError:
        pass
    return None

def check_basic_auth(authorization: str) -> tuple:
    """Check Basic Auth against admin and user credentials"""
    try:
        scheme, credentials = authorization.split(" ", 1)
        if scheme.lower() == "basic":
            decoded = base64.b64decode(credentials).decode()
            username, password = decoded.split(":", 1)
            
            # Check admin credentials
            if (settings.ADMIN_USER and settings.ADMIN_PASS and 
                username == settings.ADMIN_USER and password == settings.ADMIN_PASS):
                return True, "admin"
            
            # Check user credentials
            if username == "user" and password == "user":
                return True, "user"
                
    except (ValueError, UnicodeDecodeError):
        pass
    
    return False, None

def check_cron_auth(request: Request) -> bool:
    """Check cron authentication"""
    cron_key = request.headers.get("X-CRON-KEY")
    return cron_key == settings.CRON_KEY

async def jwt_middleware(request: Request, call_next):
    """JWT authentication middleware"""
    path = request.url.path
    
    # Skip auth for public routes
    if is_public_route(path):
        # Special case for cron endpoint
        if path == "/cron/media-retention":
            if not check_cron_auth(request):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"error": "Invalid cron key"}
                )
        
        response = await call_next(request)
        return response
    
    # Check for authorization header
    authorization = request.headers.get("Authorization")
    if not authorization:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Missing authorization header"}
        )
    
    # Try Bearer token (JWT) first
    bearer_token = extract_bearer_token(authorization)
    if bearer_token:
        user_payload = jwt_handler.verify_token(bearer_token)
        if user_payload:
            # Add user info to request state
            request.state.user = {
                "telegram_id": user_payload["telegram_id"],
                "name": user_payload["name"],
                "username": user_payload.get("username"),
                "role": user_payload["role"]
            }
            response = await call_next(request)
            return response
    
    # Try Basic Auth as fallback
    auth_valid, user_role = check_basic_auth(authorization)
    if auth_valid:
        # Add user to request state based on role
        if user_role == "admin":
            request.state.user = {
                "telegram_id": 0,  # Special admin user
                "name": "Admin",
                "username": "admin",
                "role": "admin"
            }
        else:  # user role
            request.state.user = {
                "telegram_id": -1,  # Special regular user
                "name": "User",
                "username": "user",
                "role": "user"
            }
        response = await call_next(request)
        return response
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"error": "Invalid credentials"}
    )

def require_admin(request: Request):
    """Dependency to require admin role"""
    if not hasattr(request.state, 'user'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    user = request.state.user
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    
    return user

def get_current_user(request: Request):
    """Dependency to get current user"""
    if not hasattr(request.state, 'user'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return request.state.user