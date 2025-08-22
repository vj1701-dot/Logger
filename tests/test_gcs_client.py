import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.storage.gcs_client import GCSClient

@pytest.fixture
def mock_storage_client():
    with patch('src.storage.gcs_client.storage.Client') as mock_client_class:
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        
        mock_client_class.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        yield {
            'client': mock_client,
            'bucket': mock_bucket,
            'blob': mock_blob
        }

@pytest.fixture
def gcs_client(mock_storage_client):
    return GCSClient("test-bucket")

@pytest.mark.asyncio
async def test_read_json_success(gcs_client, mock_storage_client):
    """Test successful JSON read"""
    mock_blob = mock_storage_client['blob']
    mock_blob.exists.return_value = True
    mock_blob.download_as_text.return_value = '{"test": "data"}'
    
    result = await gcs_client.read_json("test/path.json")
    
    assert result == {"test": "data"}
    mock_blob.exists.assert_called_once()
    mock_blob.download_as_text.assert_called_once()

@pytest.mark.asyncio
async def test_read_json_not_found(gcs_client, mock_storage_client):
    """Test JSON read when file doesn't exist"""
    mock_blob = mock_storage_client['blob']
    mock_blob.exists.return_value = False
    
    result = await gcs_client.read_json("nonexistent.json")
    
    assert result is None

@pytest.mark.asyncio
async def test_write_json_success(gcs_client, mock_storage_client):
    """Test successful JSON write"""
    mock_blob = mock_storage_client['blob']
    
    data = {"test": "data"}
    result = await gcs_client.write_json("test/path.json", data)
    
    assert result is True
    mock_blob.upload_from_string.assert_called_once()

@pytest.mark.asyncio
async def test_get_next_uid_first_time(gcs_client, mock_storage_client):
    """Test UID generation when counter doesn't exist"""
    mock_blob = mock_storage_client['blob']
    mock_blob.exists.return_value = False
    mock_blob.generation = 0
    
    # Mock the write operation to succeed
    with patch.object(gcs_client, 'write_json', return_value=True):
        uid = await gcs_client.get_next_uid()
    
    assert uid == "SJ0001"

@pytest.mark.asyncio
async def test_get_next_uid_existing_counter(gcs_client, mock_storage_client):
    """Test UID generation with existing counter"""
    mock_blob = mock_storage_client['blob']
    mock_blob.exists.return_value = True
    mock_blob.download_as_text.return_value = "42"
    mock_blob.generation = 123
    
    # Mock the write operation to succeed
    with patch.object(gcs_client, 'write_json', return_value=True):
        uid = await gcs_client.get_next_uid()
    
    assert uid == "SJ0043"

@pytest.mark.asyncio
async def test_get_next_uid_high_number(gcs_client, mock_storage_client):
    """Test UID generation with high numbers (no zero padding)"""
    mock_blob = mock_storage_client['blob']
    mock_blob.exists.return_value = True
    mock_blob.download_as_text.return_value = "9999"
    mock_blob.generation = 123
    
    # Mock the write operation to succeed
    with patch.object(gcs_client, 'write_json', return_value=True):
        uid = await gcs_client.get_next_uid()
    
    assert uid == "SJ10000"

@pytest.mark.asyncio
async def test_upload_media_success(gcs_client, mock_storage_client):
    """Test successful media upload"""
    mock_blob = mock_storage_client['blob']
    
    result = await gcs_client.upload_media(
        b"test data",
        "media/SJ0001/test.jpg",
        "image/jpeg"
    )
    
    assert result is True
    mock_blob.upload_from_string.assert_called_with(
        b"test data",
        content_type="image/jpeg"
    )

@pytest.mark.asyncio
async def test_create_index_marker(gcs_client, mock_storage_client):
    """Test creating index marker"""
    mock_blob = mock_storage_client['blob']
    
    result = await gcs_client.create_index_marker("index/status/new/SJ0001")
    
    assert result is True
    mock_blob.upload_from_string.assert_called_with(
        "",
        content_type='text/plain'
    )

@pytest.mark.asyncio
async def test_list_objects(gcs_client, mock_storage_client):
    """Test listing objects with prefix"""
    mock_bucket = mock_storage_client['bucket']
    
    # Mock blob list
    mock_blobs = [Mock(name="test1.json"), Mock(name="test2.json")]
    mock_blobs[0].name = "test1.json"
    mock_blobs[1].name = "test2.json"
    mock_bucket.list_blobs.return_value = mock_blobs
    
    result = await gcs_client.list_objects("test/")
    
    assert result == ["test1.json", "test2.json"]
    mock_bucket.list_blobs.assert_called_with(prefix="test/")

if __name__ == "__main__":
    pytest.main([__file__])