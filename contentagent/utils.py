"""
Storage utilities for the Multi-Agent Video Generation System.
Handles Google Cloud Storage operations with local fallback.
"""

import os
import uuid
import logging
from typing import Optional, Union
from pathlib import Path

# Ensure environment variables are loaded
from dotenv import load_dotenv
load_dotenv()

from google.cloud import storage
from google.cloud.exceptions import NotFound
from google.auth.exceptions import DefaultCredentialsError

from .config import Settings,SecretConfig

logger = logging.getLogger(__name__)

class StorageManager:
    """Manages Google Cloud Storage operations for the video generation system."""
    
    def __init__(self):
        """Initialize the storage manager with GCS client."""
        # Force reload environment variables
        load_dotenv(override=True)
        
        self.bucket_name = Settings.GCS_BUCKET_NAME
        self.project_id = SecretConfig.get_google_cloud_project() or Settings.GOOGLE_CLOUD_PROJECT
        self._bucket = None
        self._client = None
        
        logger.info(f"Initializing StorageManager with bucket: {self.bucket_name}, project: {self.project_id}")
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the GCS client with proper authentication handling."""
        try:
            # # Ensure credentials are set
            # creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            # if creds_path and os.path.exists(creds_path):
            #     logger.info(f"Using credentials from: {creds_path}")
            
            # Try to initialize GCS client
            if self.project_id:
                self._client = storage.Client(project=self.project_id)
                logger.info(f"Initialized GCS client for project: {self.project_id}")
                
                # Test client by checking if bucket exists
                if self.bucket_name:
                    test_bucket = self._client.bucket(self.bucket_name)
                    try:
                        exists = test_bucket.exists()
                        if exists:
                            logger.info(f"Successfully verified access to bucket: {self.bucket_name}")
                        else:
                            logger.error(f"Bucket {self.bucket_name} does not exist")
                            self._client = None
                    except Exception as e:
                        logger.error(f"Failed to verify bucket access: {e}")
                        self._client = None
            else:
                logger.warning("GOOGLE_CLOUD_PROJECT not set, GCS operations will be limited")
                self._client = None
        except DefaultCredentialsError as e:
            logger.warning(f"GCS authentication failed: {e}")
            logger.info("Falling back to local storage for development")
            self._client = None
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            self._client = None

    @property
    def client(self) -> Optional[storage.Client]:
        """Get the GCS client if available."""
        return self._client

    @property
    def bucket(self) -> Optional[storage.Bucket]:
        """Get or create the GCS bucket instance."""
        if not self._client:
            logger.warning("GCS client not available, cannot access bucket")
            return None
            
        if self._bucket is None and self.bucket_name:
            try:
                self._bucket = self._client.bucket(self.bucket_name)
                # Test bucket access
                self._bucket.exists()
                logger.info(f"Connected to GCS bucket: {self.bucket_name}")
            except Exception as e:
                logger.error(f"Failed to access bucket {self.bucket_name}: {e}")
                self._bucket = None
        return self._bucket

    def _fallback_local_storage(self, content: Union[str, bytes], folder: str, filename: str, content_type: str = 'text/plain') -> dict:
        """Fallback to local storage when GCS is not available."""
        import os
        
        # Create local storage directory
        local_dir = os.path.join("./output", folder)
        os.makedirs(local_dir, exist_ok=True)
        
        local_path = os.path.join(local_dir, filename)
        
        try:
            if isinstance(content, str):
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                with open(local_path, 'wb') as f:
                    f.write(content)
            
            logger.warning(f"GCS not available, saved to local storage: {local_path}")
            return {
                "blob_name": f"{folder}/{filename}",
                "local_path": local_path,
                "gcs_url": f"local://{local_path}",
                "public_url": f"file://{os.path.abspath(local_path)}",
                "status": "success",
                "storage_type": "local"
            }
        except Exception as e:
            logger.error(f"Failed to save to local storage: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def upload_text(self, content: str, folder: str, filename: Optional[str] = None) -> dict:
        """
        Upload text content to GCS or local storage.
        
        Args:
            content: Text content to upload
            folder: Folder path in the bucket
            filename: Optional filename, generates UUID if not provided
            
        Returns:
            dict: Contains blob_name, gcs_url, and public_url
        """
        if not filename:
            filename = f"{uuid.uuid4()}.txt"
        
        # Fallback to local storage if GCS not available
        if not self.bucket:
            return self._fallback_local_storage(content, folder, filename, 'text/plain')
        
        blob_name = f"{folder}/{filename}"
        blob = self.bucket.blob(blob_name)
        
        try:
            blob.upload_from_string(content, content_type='text/plain')
            logger.info(f"Uploaded text to {blob_name}")
            
            return {
                "blob_name": blob_name,
                "gcs_url": f"gs://{self.bucket_name}/{blob_name}",
                "public_url": Settings.get_public_gcs_url(blob_name),
                "status": "success",
                "storage_type": "gcs"
            }
        except Exception as e:
            logger.error(f"Failed to upload text to {blob_name}: {e}")
            # Fallback to local storage
            return self._fallback_local_storage(content, folder, filename, 'text/plain')
    
    def upload_binary(self, content: bytes, folder: str, filename: Optional[str] = None, content_type: str = 'application/octet-stream') -> dict:
        """
        Upload binary content to GCS or local storage.
        
        Args:
            content: Binary content to upload
            folder: Folder path in the bucket
            filename: Optional filename, generates UUID if not provided
            content_type: MIME type of the content
            
        Returns:
            dict: Contains blob_name, gcs_url, and public_url
        """
        if not filename:
            # Generate filename with appropriate extension based on content type
            extension = self._get_extension_from_content_type(content_type)
            filename = f"{uuid.uuid4()}{extension}"
        
        # Fallback to local storage if GCS not available
        if not self.bucket:
            return self._fallback_local_storage(content, folder, filename, content_type)
        
        blob_name = f"{folder}/{filename}"
        blob = self.bucket.blob(blob_name)
        
        try:
            blob.upload_from_string(content, content_type=content_type)
            logger.info(f"Uploaded binary content to {blob_name}")
            
            return {
                "blob_name": blob_name,
                "gcs_url": f"gs://{self.bucket_name}/{blob_name}",
                "public_url": Settings.get_public_gcs_url(blob_name),
                "content_type": content_type,
                "status": "success",
                "storage_type": "gcs"
            }
        except Exception as e:
            logger.error(f"Failed to upload binary content to {blob_name}: {e}")
            # Fallback to local storage
            return self._fallback_local_storage(content, folder, filename, content_type)
    
    def upload_file(self, file_path: str, folder: str, filename: Optional[str] = None) -> dict:
        """
        Upload a file from local filesystem to GCS.
        
        Args:
            file_path: Local path to the file
            folder: Folder path in the bucket
            filename: Optional filename, uses original if not provided
            
        Returns:
            dict: Contains blob_name, gcs_url, and public_url
        """
        if not filename:
            filename = file_path.split('/')[-1]  # Get filename from path
        
        blob_name = f"{folder}/{filename}"
        blob = self.bucket.blob(blob_name)
        
        try:
            blob.upload_from_filename(file_path)
            logger.info(f"Uploaded file {file_path} to {blob_name}")
            
            return {
                "blob_name": blob_name,
                "gcs_url": f"gs://{self.bucket_name}/{blob_name}",
                "public_url": Settings.get_public_gcs_url(blob_name),
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Failed to upload file {file_path} to {blob_name}: {e}")
            return {
                "blob_name": blob_name,
                "error": str(e),
                "status": "failed"
            }
    
    def download_as_text(self, gcs_url: str) -> str:
        """
        Download content from GCS as text.
        
        Args:
            gcs_url: GCS URL (gs://bucket/path)
            
        Returns:
            str: Text content
        """
        blob_name = self._extract_blob_name_from_url(gcs_url)
        blob = self.bucket.blob(blob_name)
        
        try:
            content = blob.download_as_text()
            logger.info(f"Downloaded text from {blob_name}")
            return content
        except NotFound:
            logger.error(f"Blob not found: {blob_name}")
            raise
        except Exception as e:
            logger.error(f"Failed to download text from {blob_name}: {e}")
            raise
    
    def download_as_bytes(self, gcs_url: str) -> bytes:
        """
        Download content from GCS as bytes.
        
        Args:
            gcs_url: GCS URL (gs://bucket/path)
            
        Returns:
            bytes: Binary content
        """
        blob_name = self._extract_blob_name_from_url(gcs_url)
        blob = self.bucket.blob(blob_name)
        
        try:
            content = blob.download_as_bytes()
            logger.info(f"Downloaded bytes from {blob_name}")
            return content
        except NotFound:
            logger.error(f"Blob not found: {blob_name}")
            raise
        except Exception as e:
            logger.error(f"Failed to download bytes from {blob_name}: {e}")
            raise
    
    def download_to_file(self, gcs_url: str, local_path: str) -> None:
        """
        Download content from GCS to local file.
        
        Args:
            gcs_url: GCS URL (gs://bucket/path)
            local_path: Local file path to save to
        """
        blob_name = self._extract_blob_name_from_url(gcs_url)
        blob = self.bucket.blob(blob_name)
        
        try:
            blob.download_to_filename(local_path)
            logger.info(f"Downloaded {blob_name} to {local_path}")
        except NotFound:
            logger.error(f"Blob not found: {blob_name}")
            raise
        except Exception as e:
            logger.error(f"Failed to download {blob_name} to {local_path}: {e}")
            raise
    
    def delete_blob(self, gcs_url: str) -> bool:
        """
        Delete a blob from GCS.
        
        Args:
            gcs_url: GCS URL (gs://bucket/path)
            
        Returns:
            bool: True if deleted successfully
        """
        blob_name = self._extract_blob_name_from_url(gcs_url)
        blob = self.bucket.blob(blob_name)
        
        try:
            blob.delete()
            logger.info(f"Deleted blob: {blob_name}")
            return True
        except NotFound:
            logger.warning(f"Blob not found for deletion: {blob_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete blob {blob_name}: {e}")
            return False
    
    def _extract_blob_name_from_url(self, gcs_url: str) -> str:
        """Extract blob name from GCS URL."""
        if gcs_url.startswith("gs://"):
            # Remove gs://bucket_name/ prefix
            parts = gcs_url[5:].split('/', 1)
            if len(parts) > 1:
                return parts[1]
            else:
                raise ValueError(f"Invalid GCS URL format: {gcs_url}")
        else:
            raise ValueError(f"URL must start with gs://: {gcs_url}")
    
    def _get_extension_from_content_type(self, content_type: str) -> str:
        """Get file extension from content type."""
        content_type_map = {
            'audio/mpeg': '.mp3',
            'audio/mp3': '.mp3',
            'image/png': '.png',
            'image/jpeg': '.jpg',
            'video/mp4': '.mp4',
            'application/json': '.json',
            'text/plain': '.txt'
        }
        return content_type_map.get(content_type, '')

# Global storage manager instance
try:
    storage_manager = StorageManager()
    logger.info("Storage manager initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize storage manager: {e}")
    # Create a minimal storage manager for development
    storage_manager = None 