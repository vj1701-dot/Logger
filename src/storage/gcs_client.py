import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from io import BytesIO

from google.cloud import storage
from google.cloud.exceptions import NotFound, PreconditionFailed
from google.api_core.exceptions import RetryError

logger = logging.getLogger(__name__)

class GCSClient:
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
    
    async def read_json(self, path: str) -> Optional[Dict]:
        """Read JSON object from GCS"""
        try:
            blob = self.bucket.blob(path)
            if not blob.exists():
                return None
            
            content = blob.download_as_text()
            return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to read JSON from {path}: {e}")
            return None
    
    async def write_json(self, path: str, data: Dict, if_generation_match: Optional[int] = None) -> bool:
        """Write JSON object to GCS with optional conditional write"""
        try:
            blob = self.bucket.blob(path)
            content = json.dumps(data, indent=2, default=str)
            
            if if_generation_match is not None:
                blob.upload_from_string(
                    content, 
                    content_type='application/json',
                    if_generation_match=if_generation_match
                )
            else:
                blob.upload_from_string(content, content_type='application/json')
            
            return True
        except PreconditionFailed:
            logger.warning(f"Conditional write failed for {path}")
            return False
        except Exception as e:
            logger.error(f"Failed to write JSON to {path}: {e}")
            return False
    
    async def append_jsonl(self, path: str, data: Dict) -> bool:
        """Append JSON line to a JSONL file"""
        try:
            # Read existing content
            blob = self.bucket.blob(path)
            existing_content = ""
            if blob.exists():
                existing_content = blob.download_as_text()
            
            # Append new line
            new_line = json.dumps(data, default=str) + "\n"
            updated_content = existing_content + new_line
            
            blob.upload_from_string(updated_content, content_type='application/json')
            return True
        except Exception as e:
            logger.error(f"Failed to append to JSONL {path}: {e}")
            return False
    
    async def upload_media(self, file_data: bytes, path: str, content_type: str) -> bool:
        """Upload media file to GCS"""
        try:
            blob = self.bucket.blob(path)
            blob.upload_from_string(file_data, content_type=content_type)
            return True
        except Exception as e:
            logger.error(f"Failed to upload media to {path}: {e}")
            return False
    
    async def download_media(self, path: str) -> Optional[bytes]:
        """Download media file from GCS"""
        try:
            blob = self.bucket.blob(path)
            if not blob.exists():
                return None
            return blob.download_as_bytes()
        except Exception as e:
            logger.error(f"Failed to download media from {path}: {e}")
            return None
    
    async def delete_object(self, path: str) -> bool:
        """Delete object from GCS"""
        try:
            blob = self.bucket.blob(path)
            if blob.exists():
                blob.delete()
            return True
        except Exception as e:
            logger.error(f"Failed to delete {path}: {e}")
            return False
    
    async def list_objects(self, prefix: str) -> List[str]:
        """List objects with given prefix"""
        try:
            blobs = self.bucket.list_blobs(prefix=prefix)
            return [blob.name for blob in blobs]
        except Exception as e:
            logger.error(f"Failed to list objects with prefix {prefix}: {e}")
            return []
    
    async def create_index_marker(self, path: str) -> bool:
        """Create zero-byte marker file for indexing"""
        try:
            blob = self.bucket.blob(path)
            blob.upload_from_string("", content_type='text/plain')
            return True
        except Exception as e:
            logger.error(f"Failed to create index marker {path}: {e}")
            return False
    
    async def delete_index_marker(self, path: str) -> bool:
        """Delete index marker"""
        return await self.delete_object(path)
    
    async def get_next_uid(self) -> str:
        """Get next sequential UID using atomic counter"""
        counter_path = "counters/uid.seq"
        max_retries = 5
        
        for attempt in range(max_retries):
            try:
                # Try to read current counter
                blob = self.bucket.blob(counter_path)
                
                if blob.exists():
                    current_content = blob.download_as_text().strip()
                    current_num = int(current_content) if current_content else 0
                    generation = blob.generation
                else:
                    current_num = 0
                    generation = 0
                
                next_num = current_num + 1
                
                # Format UID
                if next_num <= 9999:
                    uid = f"SJ{next_num:04d}"
                else:
                    uid = f"SJ{next_num}"
                
                # Atomic write with generation check
                if await self.write_json(counter_path, next_num, if_generation_match=generation):
                    return uid
                
                # If write failed, retry
                logger.warning(f"UID generation attempt {attempt + 1} failed, retrying...")
                
            except Exception as e:
                logger.error(f"UID generation error on attempt {attempt + 1}: {e}")
        
        raise Exception("Failed to generate UID after maximum retries")
    
    async def get_blob_metadata(self, path: str) -> Optional[Dict]:
        """Get blob metadata"""
        try:
            blob = self.bucket.blob(path)
            if not blob.exists():
                return None
            
            blob.reload()
            return {
                'size': blob.size,
                'content_type': blob.content_type,
                'time_created': blob.time_created.isoformat() if blob.time_created else None,
                'updated': blob.updated.isoformat() if blob.updated else None,
                'generation': blob.generation,
                'etag': blob.etag
            }
        except Exception as e:
            logger.error(f"Failed to get metadata for {path}: {e}")
            return None