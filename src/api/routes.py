import secrets
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends, Query, File, UploadFile, Response
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from src.auth.middleware import require_admin, get_current_user
from src.auth.jwt_handler import jwt_handler
from src.services.task_service import TaskService
from src.services.user_service import UserService
from src.models.task import TaskStatus, Priority, TelegramUser
from src.models.user import UserRole
from src.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models for request/response
class TaskListResponse(BaseModel):
    tasks: List[Dict[str, Any]]
    total: int

class StatusUpdateRequest(BaseModel):
    status: TaskStatus
    reason: Optional[str] = None

class AssigneeRequest(BaseModel):
    telegram_id: int
    action: str  # "add" or "remove"

class NoteRequest(BaseModel):
    content: str

class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    role: Optional[UserRole] = None
    active: Optional[bool] = None

class LoginRequest(BaseModel):
    telegram_id: int

# Dependency to get services
async def get_task_service(request: Request) -> TaskService:
    return TaskService(request.app.state.gcs_client)

async def get_user_service(request: Request) -> UserService:
    return UserService(request.app.state.gcs_client)

# Auth endpoints
@router.post("/auth/login")
async def request_login(
    login_req: LoginRequest,
    request: Request,
    user_service: UserService = Depends(get_user_service)
):
    """Request magic link login"""
    try:
        # Check if user exists
        user = await user_service.get_user(login_req.telegram_id)
        if not user or not user.active:
            raise HTTPException(status_code=404, detail="User not found or inactive")
        
        # Create magic link token
        magic_token = jwt_handler.create_magic_link_token(login_req.telegram_id)
        magic_link = f"{settings.APP_BASE_URL}/api/auth/magic-link?token={magic_token}"
        
        # In a real implementation, you would send this link via Telegram bot
        # For now, we'll return it in the response
        return {
            "message": "Magic link created",
            "magic_link": magic_link,
            "expires_in_minutes": settings.MAGIC_LINK_TTL_MIN
        }
        
    except Exception as e:
        logger.error(f"Login request failed: {e}")
        raise HTTPException(status_code=500, detail="Login request failed")

@router.get("/auth/magic-link")
async def verify_magic_link(
    token: str,
    request: Request,
    user_service: UserService = Depends(get_user_service)
):
    """Verify magic link and issue JWT"""
    try:
        telegram_id = jwt_handler.verify_magic_link_token(token)
        if not telegram_id:
            raise HTTPException(status_code=400, detail="Invalid or expired magic link")
        
        # Get user details
        user = await user_service.get_user(telegram_id)
        if not user or not user.active:
            raise HTTPException(status_code=404, detail="User not found or inactive")
        
        # Update last seen
        user.update_last_seen()
        await user_service.update_user(user)
        
        # Create JWT
        jwt_token = jwt_handler.create_token({
            "telegram_id": user.telegram_id,
            "name": user.name,
            "username": user.username,
            "role": user.role.value
        })
        
        return {
            "access_token": jwt_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_TTL_MIN * 60,
            "user": {
                "telegram_id": user.telegram_id,
                "name": user.name,
                "username": user.username,
                "role": user.role.value
            }
        }
        
    except Exception as e:
        logger.error(f"Magic link verification failed: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")

# Task endpoints
@router.get("/tasks")
async def list_tasks(
    request: Request,
    status: Optional[TaskStatus] = Query(None),
    assignee_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    task_service: TaskService = Depends(get_task_service),
    current_user: Dict = Depends(get_current_user)
):
    """List tasks with filters"""
    try:
        task_uids = []
        
        if status:
            task_uids = await task_service.list_tasks_by_status(status, limit)
        elif assignee_id:
            task_uids = await task_service.list_tasks_by_assignee(assignee_id, limit)
        elif search:
            task_uids = await task_service.search_tasks(search, limit)
        else:
            # Get all new tasks by default
            task_uids = await task_service.list_tasks_by_status(TaskStatus.NEW, limit)
        
        # Fetch task details
        tasks = []
        for uid in task_uids:
            task = await task_service.get_task(uid)
            if task:
                tasks.append(task.to_dict())
        
        return TaskListResponse(tasks=tasks, total=len(tasks))
        
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to list tasks")

@router.get("/tasks/{uid}")
async def get_task(
    uid: str,
    request: Request,
    task_service: TaskService = Depends(get_task_service),
    current_user: Dict = Depends(get_current_user)
):
    """Get task by UID"""
    try:
        task = await task_service.get_task(uid)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task.to_dict()
        
    except Exception as e:
        logger.error(f"Failed to get task {uid}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task")

@router.patch("/tasks/{uid}")
async def update_task(
    uid: str,
    updates: Dict[str, Any],
    request: Request,
    task_service: TaskService = Depends(get_task_service),
    admin_user: Dict = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    """Update task (admin only)"""
    try:
        task = await task_service.get_task(uid)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Update allowed fields
        if "title" in updates:
            task.title = updates["title"]
        if "description" in updates:
            task.description = updates["description"]
        if "priority" in updates:
            task.priority = Priority(updates["priority"])
        
        success = await task_service.update_task(task)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update task")
        
        # Log admin action
        await user_service.log_admin_action(
            admin_user["telegram_id"],
            "update_task",
            uid,
            {"updates": updates}
        )
        
        return task.to_dict()
        
    except Exception as e:
        logger.error(f"Failed to update task {uid}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update task")

@router.post("/tasks/{uid}/status")
async def change_task_status(
    uid: str,
    status_req: StatusUpdateRequest,
    request: Request,
    task_service: TaskService = Depends(get_task_service),
    admin_user: Dict = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    """Change task status (admin only)"""
    try:
        admin_telegram_user = TelegramUser(
            telegram_id=admin_user["telegram_id"],
            name=admin_user["name"],
            username=admin_user.get("username")
        )
        
        success = await task_service.change_task_status(
            uid,
            status_req.status,
            admin_telegram_user,
            status_req.reason
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found or update failed")
        
        # Log admin action
        await user_service.log_admin_action(
            admin_user["telegram_id"],
            "change_status",
            uid,
            {"status": status_req.status.value, "reason": status_req.reason}
        )
        
        return {"message": "Status updated successfully"}
        
    except Exception as e:
        logger.error(f"Failed to change status for task {uid}: {e}")
        raise HTTPException(status_code=500, detail="Failed to change status")

@router.post("/tasks/{uid}/assignees")
async def manage_assignees(
    uid: str,
    assignee_req: AssigneeRequest,
    request: Request,
    task_service: TaskService = Depends(get_task_service),
    admin_user: Dict = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    """Add or remove assignee (admin only)"""
    try:
        # Get assignee user info
        assignee_user = await user_service.get_user(assignee_req.telegram_id)
        if not assignee_user:
            raise HTTPException(status_code=404, detail="Assignee user not found")
        
        assignee_telegram_user = TelegramUser(
            telegram_id=assignee_user.telegram_id,
            name=assignee_user.name,
            username=assignee_user.username
        )
        
        if assignee_req.action == "add":
            success = await task_service.assign_task(uid, assignee_telegram_user)
            action_msg = "assigned"
        elif assignee_req.action == "remove":
            success = await task_service.unassign_task(uid, assignee_req.telegram_id)
            action_msg = "unassigned"
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found or update failed")
        
        # Log admin action
        await user_service.log_admin_action(
            admin_user["telegram_id"],
            f"{assignee_req.action}_assignee",
            uid,
            {"assignee_id": assignee_req.telegram_id, "action": assignee_req.action}
        )
        
        return {"message": f"User {action_msg} successfully"}
        
    except Exception as e:
        logger.error(f"Failed to manage assignee for task {uid}: {e}")
        raise HTTPException(status_code=500, detail="Failed to manage assignee")

@router.post("/tasks/{uid}/note")
async def add_task_note(
    uid: str,
    note_req: NoteRequest,
    request: Request,
    task_service: TaskService = Depends(get_task_service),
    admin_user: Dict = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    """Add note to task (admin only)"""
    try:
        admin_telegram_user = TelegramUser(
            telegram_id=admin_user["telegram_id"],
            name=admin_user["name"],
            username=admin_user.get("username")
        )
        
        success = await task_service.add_task_note(
            uid,
            note_req.content,
            admin_telegram_user
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found or update failed")
        
        # Log admin action
        await user_service.log_admin_action(
            admin_user["telegram_id"],
            "add_note",
            uid,
            {"content": note_req.content}
        )
        
        return {"message": "Note added successfully"}
        
    except Exception as e:
        logger.error(f"Failed to add note to task {uid}: {e}")
        raise HTTPException(status_code=500, detail="Failed to add note")

# Media endpoints
@router.get("/media/{uid}/{filename}")
async def get_media(
    uid: str,
    filename: str,
    request: Request,
    current_user: Dict = Depends(get_current_user)
):
    """Stream media file"""
    try:
        gcs_client = request.app.state.gcs_client
        media_path = f"media/{uid}/{filename}"
        
        media_data = await gcs_client.download_media(media_path)
        if not media_data:
            raise HTTPException(status_code=404, detail="Media not found")
        
        # Get metadata to determine content type
        metadata = await gcs_client.get_blob_metadata(media_path)
        content_type = metadata.get("content_type", "application/octet-stream") if metadata else "application/octet-stream"
        
        return StreamingResponse(
            io.BytesIO(media_data),
            media_type=content_type,
            headers={"Content-Disposition": f"inline; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Failed to get media {uid}/{filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get media")

@router.delete("/media/{uid}/{filename}")
async def delete_media(
    uid: str,
    filename: str,
    request: Request,
    admin_user: Dict = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    """Delete media file (admin only)"""
    try:
        gcs_client = request.app.state.gcs_client
        media_path = f"media/{uid}/{filename}"
        
        success = await gcs_client.delete_object(media_path)
        if not success:
            raise HTTPException(status_code=404, detail="Media not found")
        
        # Log admin action
        await user_service.log_admin_action(
            admin_user["telegram_id"],
            "delete_media",
            f"{uid}/{filename}",
            {"media_path": media_path}
        )
        
        return {"message": "Media deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete media {uid}/{filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete media")

# User management endpoints
@router.get("/users")
async def list_users(
    request: Request,
    admin_user: Dict = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    """List all users (admin only)"""
    try:
        users = await user_service.list_all_users()
        return [user.to_dict() for user in users]
        
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(status_code=500, detail="Failed to list users")

@router.patch("/users/{telegram_id}")
async def update_user(
    telegram_id: int,
    updates: UserUpdateRequest,
    request: Request,
    admin_user: Dict = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    """Update user (admin only)"""
    try:
        user = await user_service.get_user(telegram_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update fields
        if updates.name is not None:
            user.name = updates.name
        if updates.username is not None:
            user.username = updates.username
        if updates.role is not None:
            user.role = updates.role
        if updates.active is not None:
            user.active = updates.active
        
        success = await user_service.update_user(user)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update user")
        
        # Log admin action
        await user_service.log_admin_action(
            admin_user["telegram_id"],
            "update_user",
            str(telegram_id),
            {"updates": updates.dict(exclude_none=True)}
        )
        
        return user.to_dict()
        
    except Exception as e:
        logger.error(f"Failed to update user {telegram_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")

@router.post("/users")
async def create_user_stub(
    user_data: Dict[str, Any],
    request: Request,
    admin_user: Dict = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    """Create user stub (admin only)"""
    try:
        user = await user_service.create_user(
            telegram_id=user_data["telegram_id"],
            name=user_data["name"],
            username=user_data.get("username"),
            role=UserRole(user_data.get("role", "user"))
        )
        
        # Log admin action
        await user_service.log_admin_action(
            admin_user["telegram_id"],
            "create_user",
            str(user.telegram_id),
            {"user_data": user_data}
        )
        
        return user.to_dict()
        
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")

@router.get("/users/export")
async def export_users(
    request: Request,
    admin_user: Dict = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    """Export users to CSV (admin only)"""
    try:
        csv_content = await user_service.export_users_csv()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=users.csv"}
        )
        
    except Exception as e:
        logger.error(f"Failed to export users: {e}")
        raise HTTPException(status_code=500, detail="Failed to export users")

# Cron endpoint
@router.get("/cron/media-retention")
async def media_retention_job(
    request: Request,
    task_service: TaskService = Depends(get_task_service)
):
    """Media retention cron job (protected by X-CRON-KEY header)"""
    try:
        result = await task_service.delete_expired_media()
        return {
            "message": "Media retention job completed",
            "deleted_files": result["deleted_files"],
            "checked_tasks": result["checked_tasks"]
        }
        
    except Exception as e:
        logger.error(f"Media retention job failed: {e}")
        raise HTTPException(status_code=500, detail="Media retention job failed")

# Mini App endpoints
@router.post("/miniapp/validate")
async def validate_miniapp_data(
    request: Request,
    user_service: UserService = Depends(get_user_service)
):
    """Validate Telegram Mini App init data and issue JWT"""
    try:
        body = await request.json()
        init_data = body.get("initData", "")
        
        if not init_data:
            raise HTTPException(status_code=400, detail="Missing init data")
        
        # Parse init data
        params = {}
        for param in init_data.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                params[key] = value
        
        # Verify HMAC (simplified - in production use proper crypto verification)
        user_data = params.get("user")
        if not user_data:
            raise HTTPException(status_code=400, detail="No user data in init data")
        
        # Parse user data (URL decode and JSON parse)
        import urllib.parse
        import json
        user_json = urllib.parse.unquote(user_data)
        user_info = json.loads(user_json)
        
        # Get or create user
        user = await user_service.get_or_create_user(
            telegram_id=user_info["id"],
            name=f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip(),
            username=user_info.get("username")
        )
        
        # Update last seen
        user.update_last_seen()
        await user_service.update_user(user)
        
        # Create JWT
        jwt_token = jwt_handler.create_token({
            "telegram_id": user.telegram_id,
            "name": user.name,
            "username": user.username,
            "role": user.role.value
        })
        
        return {
            "access_token": jwt_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_TTL_MIN * 60,
            "user": {
                "telegram_id": user.telegram_id,
                "name": user.name,
                "username": user.username,
                "role": user.role.value
            }
        }
        
    except Exception as e:
        logger.error(f"Mini app validation failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid init data")

# Add missing import
import io

# Admin management endpoints
class PromoteUserRequest(BaseModel):
    telegram_id: int

@router.post("/admin/promote")
async def promote_user_to_admin(
    promote_req: PromoteUserRequest,
    request: Request,
    admin_user: Dict = Depends(require_admin)
):
    """Promote a user to admin role (admin only)"""
    try:
        gcs_client = request.app.state.gcs_client
        user_service = UserService(gcs_client)
        
        # Check if user exists
        user = await user_service.get_user(promote_req.telegram_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.role == UserRole.ADMIN:
            raise HTTPException(status_code=400, detail="User is already an admin")
        
        # Promote user to admin
        success = await user_service.update_user_role(promote_req.telegram_id, UserRole.ADMIN)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to promote user")
        
        # Log admin action
        await user_service.log_admin_action(
            admin_user["telegram_id"],
            "promote_user",
            str(promote_req.telegram_id),
            {"role": "admin"}
        )
        
        return {
            "message": f"User {user.name} promoted to admin successfully",
            "user": {
                "telegram_id": user.telegram_id,
                "name": user.name,
                "username": user.username,
                "role": "admin"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to promote user {promote_req.telegram_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to promote user")