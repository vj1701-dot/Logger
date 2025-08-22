import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from src.services.task_service import TaskService
from src.models.task import Task, TaskStatus, TelegramUser
from src.storage.gcs_client import GCSClient

@pytest.fixture
def mock_gcs_client():
    client = Mock(spec=GCSClient)
    client.get_next_uid = AsyncMock(return_value="SJ0001")
    client.write_json = AsyncMock(return_value=True)
    client.create_index_marker = AsyncMock(return_value=True)
    client.read_json = AsyncMock()
    client.upload_media = AsyncMock(return_value=True)
    return client

@pytest.fixture
def task_service(mock_gcs_client):
    return TaskService(mock_gcs_client)

@pytest.fixture
def sample_user():
    return TelegramUser(
        telegram_id=12345,
        name="Test User",
        username="testuser"
    )

@pytest.mark.asyncio
async def test_create_task(task_service, mock_gcs_client, sample_user):
    """Test task creation with UID generation"""
    task = await task_service.create_task(
        title="Test Task",
        description="Test Description",
        created_by=sample_user
    )
    
    assert task.uid == "SJ0001"
    assert task.title == "Test Task"
    assert task.description == "Test Description"
    assert task.created_by == sample_user
    assert task.status == TaskStatus.NEW
    
    # Verify GCS calls
    mock_gcs_client.get_next_uid.assert_called_once()
    mock_gcs_client.write_json.assert_called_once()

@pytest.mark.asyncio
async def test_create_task_with_media(task_service, mock_gcs_client, sample_user):
    """Test task creation with media files"""
    media_files = [{
        'type': 'photo',
        'filename': 'test.jpg',
        'content_type': 'image/jpeg',
        'data': b'fake image data'
    }]
    
    task = await task_service.create_task(
        title="Task with Media",
        description="Description",
        created_by=sample_user,
        media_files=media_files
    )
    
    assert len(task.media) == 1
    assert task.media[0].path == "media/SJ0001/test.jpg"
    mock_gcs_client.upload_media.assert_called_once()

@pytest.mark.asyncio
async def test_get_task(task_service, mock_gcs_client):
    """Test retrieving task by UID"""
    # Mock task data
    task_data = {
        "uid": "SJ0001",
        "title": "Test Task",
        "description": "Test Description",
        "status": "new",
        "priority": "medium",
        "assignees": [],
        "notes": [],
        "media": [],
        "statusHistory": [],
        "timestamps": {
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z"
        }
    }
    mock_gcs_client.read_json.return_value = task_data
    
    task = await task_service.get_task("SJ0001")
    
    assert task is not None
    assert task.uid == "SJ0001"
    assert task.title == "Test Task"
    mock_gcs_client.read_json.assert_called_with("tasks/SJ0001.json")

@pytest.mark.asyncio
async def test_get_nonexistent_task(task_service, mock_gcs_client):
    """Test retrieving non-existent task returns None"""
    mock_gcs_client.read_json.return_value = None
    
    task = await task_service.get_task("SJ9999")
    
    assert task is None

@pytest.mark.asyncio
async def test_change_task_status(task_service, mock_gcs_client, sample_user):
    """Test changing task status"""
    # Mock existing task
    task_data = {
        "uid": "SJ0001",
        "title": "Test Task",
        "description": "Test Description",
        "status": "new",
        "priority": "medium",
        "assignees": [],
        "notes": [],
        "media": [],
        "statusHistory": [],
        "timestamps": {
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z"
        }
    }
    mock_gcs_client.read_json.return_value = task_data
    
    success = await task_service.change_task_status(
        "SJ0001",
        TaskStatus.IN_PROGRESS,
        sample_user
    )
    
    assert success is True
    mock_gcs_client.write_json.assert_called()

if __name__ == "__main__":
    pytest.main([__file__])