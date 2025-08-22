import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from src.storage.gcs_client import GCSClient
from src.models.task import Task, TaskStatus, TelegramUser
from src.models.user import User

logger = logging.getLogger(__name__)

class TaskService:
    def __init__(self, gcs_client: GCSClient):
        self.gcs = gcs_client
    
    async def create_task(
        self, 
        title: str, 
        description: str, 
        created_by: TelegramUser,
        media_files: Optional[List[Dict[str, Any]]] = None
    ) -> Task:
        """Create a new task with sequential UID"""
        try:
            # Generate sequential UID
            uid = await self.gcs.get_next_uid()
            
            # Create task
            task = Task(
                uid=uid,
                title=title,
                description=description,
                created_by=created_by
            )
            
            # Handle media files
            if media_files:
                for media_info in media_files:
                    media_path = f"media/{uid}/{media_info['filename']}"
                    success = await self.gcs.upload_media(
                        media_info['data'],
                        media_path,
                        media_info['content_type']
                    )
                    
                    if success:
                        from src.models.task import MediaItem, MediaType
                        media_item = MediaItem(
                            type=MediaType(media_info['type']),
                            path=media_path,
                            metadata={
                                'filename': media_info['filename'],
                                'size': len(media_info['data']),
                                'content_type': media_info['content_type']
                            }
                        )
                        task.media.append(media_item)
            
            # Save task
            task_path = f"tasks/{uid}.json"
            await self.gcs.write_json(task_path, task.to_dict())
            
            # Create index markers
            await self._create_task_indices(task)
            
            logger.info(f"Created task {uid}")
            return task
            
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise
    
    async def get_task(self, uid: str) -> Optional[Task]:
        """Get task by UID"""
        try:
            task_path = f"tasks/{uid}.json"
            data = await self.gcs.read_json(task_path)
            if not data:
                return None
            
            return Task.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to get task {uid}: {e}")
            return None
    
    async def update_task(self, task: Task) -> bool:
        """Update task and indices"""
        try:
            task.updated_at = datetime.now(timezone.utc)
            task_path = f"tasks/{task.uid}.json"
            
            success = await self.gcs.write_json(task_path, task.to_dict())
            if success:
                await self._update_task_indices(task)
                logger.info(f"Updated task {task.uid}")
            
            return success
        except Exception as e:
            logger.error(f"Failed to update task {task.uid}: {e}")
            return False
    
    async def change_task_status(
        self, 
        uid: str, 
        new_status: TaskStatus, 
        changed_by: TelegramUser,
        reason: Optional[str] = None
    ) -> bool:
        """Change task status with history tracking"""
        task = await self.get_task(uid)
        if not task:
            return False
        
        old_status = task.status
        task.change_status(new_status, changed_by, reason)
        
        # Set deletion date for media when task is done
        if new_status == TaskStatus.DONE and task.media:
            deletion_date = datetime.now(timezone.utc) + timedelta(days=7)
            for media_item in task.media:
                media_item.delete_after = deletion_date
        
        success = await self.update_task(task)
        if success:
            # Update status index
            await self._update_status_index(task, old_status, new_status)
        
        return success
    
    async def assign_task(self, uid: str, assignee: TelegramUser) -> bool:
        """Assign task to user"""
        task = await self.get_task(uid)
        if not task:
            return False
        
        task.add_assignee(assignee)
        success = await self.update_task(task)
        
        if success:
            # Create assignee index
            await self._create_assignee_index(task.uid, assignee.telegram_id)
        
        return success
    
    async def unassign_task(self, uid: str, telegram_id: int) -> bool:
        """Unassign task from user"""
        task = await self.get_task(uid)
        if not task:
            return False
        
        task.remove_assignee(telegram_id)
        success = await self.update_task(task)
        
        if success:
            # Remove assignee index
            await self._remove_assignee_index(task.uid, telegram_id)
        
        return success
    
    async def add_task_note(
        self, 
        uid: str, 
        content: str, 
        author: TelegramUser,
        media_file: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add note to task"""
        task = await self.get_task(uid)
        if not task:
            return False
        
        media_item = None
        if media_file:
            media_path = f"media/{uid}/notes/{media_file['filename']}"
            success = await self.gcs.upload_media(
                media_file['data'],
                media_path,
                media_file['content_type']
            )
            
            if success:
                from src.models.task import MediaItem, MediaType
                media_item = MediaItem(
                    type=MediaType(media_file['type']),
                    path=media_path,
                    metadata={
                        'filename': media_file['filename'],
                        'size': len(media_file['data']),
                        'content_type': media_file['content_type']
                    }
                )
        
        task.add_note(content, author, media_item)
        return await self.update_task(task)
    
    async def list_tasks_by_status(self, status: TaskStatus, limit: int = 100) -> List[str]:
        """List task UIDs by status using index"""
        try:
            prefix = f"index/status/{status.value}/"
            paths = await self.gcs.list_objects(prefix)
            
            # Extract UIDs from paths and limit
            uids = []
            for path in paths:
                uid = path.split('/')[-1]
                if uid:
                    uids.append(uid)
                if len(uids) >= limit:
                    break
            
            return uids
        except Exception as e:
            logger.error(f"Failed to list tasks by status {status}: {e}")
            return []
    
    async def list_tasks_by_assignee(self, telegram_id: int, limit: int = 100) -> List[str]:
        """List task UIDs by assignee using index"""
        try:
            prefix = f"index/assignee/{telegram_id}/"
            paths = await self.gcs.list_objects(prefix)
            
            # Extract UIDs from paths and limit
            uids = []
            for path in paths:
                uid = path.split('/')[-1]
                if uid:
                    uids.append(uid)
                if len(uids) >= limit:
                    break
            
            return uids
        except Exception as e:
            logger.error(f"Failed to list tasks by assignee {telegram_id}: {e}")
            return []
    
    async def search_tasks(self, query: str, limit: int = 100) -> List[str]:
        """Search tasks by title/description (fallback to full scan)"""
        try:
            # This is a simplified search - in production you might want
            # to implement proper text search indexing
            all_task_paths = await self.gcs.list_objects("tasks/")
            matching_uids = []
            
            query_lower = query.lower()
            
            for path in all_task_paths:
                if not path.endswith('.json'):
                    continue
                
                task_data = await self.gcs.read_json(path)
                if not task_data:
                    continue
                
                # Check UID, title, description
                if (query_lower in task_data.get('uid', '').lower() or
                    query_lower in task_data.get('title', '').lower() or
                    query_lower in task_data.get('description', '').lower()):
                    
                    matching_uids.append(task_data['uid'])
                    if len(matching_uids) >= limit:
                        break
            
            return matching_uids
        except Exception as e:
            logger.error(f"Failed to search tasks: {e}")
            return []
    
    async def delete_expired_media(self) -> Dict[str, int]:
        """Delete media files that have passed their deletion date"""
        try:
            deleted_count = 0
            checked_count = 0
            current_time = datetime.now(timezone.utc)
            
            # Get all task files
            task_paths = await self.gcs.list_objects("tasks/")
            
            for path in task_paths:
                if not path.endswith('.json'):
                    continue
                
                task_data = await self.gcs.read_json(path)
                if not task_data:
                    continue
                
                checked_count += 1
                media_to_remove = []
                
                # Check each media item
                for i, media_data in enumerate(task_data.get('media', [])):
                    delete_after = media_data.get('deleteAfter')
                    if delete_after:
                        delete_time = datetime.fromisoformat(delete_after)
                        if current_time >= delete_time:
                            # Delete the media file
                            media_path = media_data['path']
                            if await self.gcs.delete_object(media_path):
                                media_to_remove.append(i)
                                deleted_count += 1
                                logger.info(f"Deleted expired media: {media_path}")
                
                # Update task if media was removed
                if media_to_remove:
                    # Remove media entries (in reverse order to maintain indices)
                    for i in reversed(media_to_remove):
                        task_data['media'].pop(i)
                    
                    # Update task file
                    await self.gcs.write_json(path, task_data)
            
            return {
                "deleted_files": deleted_count,
                "checked_tasks": checked_count
            }
            
        except Exception as e:
            logger.error(f"Failed to delete expired media: {e}")
            return {"deleted_files": 0, "checked_tasks": 0}
    
    # Index management methods
    async def _create_task_indices(self, task: Task):
        """Create index markers for new task"""
        # Status index
        status_path = f"index/status/{task.status.value}/{task.uid}"
        await self.gcs.create_index_marker(status_path)
        
        # Assignee indices
        for assignee in task.assignees:
            assignee_path = f"index/assignee/{assignee.telegram_id}/{task.uid}"
            await self.gcs.create_index_marker(assignee_path)
    
    async def _update_task_indices(self, task: Task):
        """Update indices for existing task"""
        # Note: This is a simplified approach. In production, you might want
        # to track previous state to avoid recreating all indices
        await self._create_task_indices(task)
    
    async def _update_status_index(self, task: Task, old_status: TaskStatus, new_status: TaskStatus):
        """Update status index when status changes"""
        if old_status != new_status:
            # Remove old status index
            old_path = f"index/status/{old_status.value}/{task.uid}"
            await self.gcs.delete_index_marker(old_path)
            
            # Create new status index
            new_path = f"index/status/{new_status.value}/{task.uid}"
            await self.gcs.create_index_marker(new_path)
    
    async def _create_assignee_index(self, uid: str, telegram_id: int):
        """Create assignee index marker"""
        path = f"index/assignee/{telegram_id}/{uid}"
        await self.gcs.create_index_marker(path)
    
    async def _remove_assignee_index(self, uid: str, telegram_id: int):
        """Remove assignee index marker"""
        path = f"index/assignee/{telegram_id}/{uid}"
        await self.gcs.delete_index_marker(path)
    
    async def delete_task(self, uid: str) -> bool:
        """Delete a task and all its indices"""
        try:
            # Get task first to clean up indices
            task = await self.get_task(uid)
            if not task:
                return False
            
            # Remove from status index
            status_index_path = f"index/status/{task.status.value}/{uid}"
            await self.gcs.delete_index_marker(status_index_path)
            
            # Remove from assignee indices
            if task.assignees:
                for assignee in task.assignees:
                    await self._remove_assignee_index(uid, assignee.telegram_id)
            
            # Delete the main task file
            task_path = f"tasks/{uid}.json"
            success = await self.gcs.delete_blob(task_path)
            
            if success:
                logger.info(f"Task {uid} deleted successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete task {uid}: {e}")
            return False