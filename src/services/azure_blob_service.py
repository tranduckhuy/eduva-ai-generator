"""
Azure Blob Storage service for file upload/download operations
"""
import os
import asyncio
import tempfile
from typing import Optional
from azure.storage.blob import BlobServiceClient
from src.utils.logger import logger


class AzureBlobService:
    """Service for handling Azure Blob Storage operations"""
    
    def __init__(self, connection_string: str):
        """Initialize Azure Blob Service"""
        self.connection_string = connection_string
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
    async def upload_file(self, container_name: str, blob_name: str, file_path: str, 
                         content_type: Optional[str] = None) -> str:
        try:
            # Ensure container exists
            await self._ensure_container_exists(container_name)
            
            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, 
                blob=blob_name
            )
            
            # Upload file
            with open(file_path, 'rb') as data:
                await asyncio.to_thread(
                    blob_client.upload_blob,
                    data,
                    overwrite=True,
                    content_type=content_type
                )
            
            blob_url = blob_client.url
            logger.info(f"Successfully uploaded file to Azure Blob: {blob_url}")
            return blob_url
            
        except Exception as e:
            logger.error(f"Failed to upload file to Azure Blob: {e}")
            raise
    
    async def download_file(
            self, container_name: str, 
            blob_name: str,
            local_path: Optional[str] = None) -> str:
        try:
            # Create local path if not provided
            if local_path is None:
                local_path = os.path.join(tempfile.gettempdir(), blob_name)
            
            # Ensure local directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            # Download file
            with open(local_path, 'wb') as download_file:
                download_stream = await asyncio.to_thread(blob_client.download_blob)
                await asyncio.to_thread(download_stream.readinto, download_file)
            
            logger.info(f"Successfully downloaded file from Azure Blob: {local_path}")
            return local_path
            
        except Exception as e:
            logger.error(f"Failed to download file from Azure Blob: {e}")
            raise
    
    async def upload_content(self, container_name: str, blob_name: str, content: bytes,
                            content_type: Optional[str] = None) -> str:
        try:
            # Ensure container exists
            await self._ensure_container_exists(container_name)
            
            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            # Upload content
            await asyncio.to_thread(
                blob_client.upload_blob,
                content,
                overwrite=True,
                content_type=content_type
            )
            
            blob_url = blob_client.url
            logger.info(f"Successfully uploaded content to Azure Blob: {blob_url}")
            return blob_url
            
        except Exception as e:
            logger.error(f"Failed to upload content to Azure Blob: {e}")
            raise
    
    async def blob_exists(self, container_name: str, blob_name: str) -> bool:
        """Check if a blob exists"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            return await asyncio.to_thread(blob_client.exists)
        except Exception:
            return False
    
    async def delete_blob(self, container_name: str, blob_name: str) -> bool:
        """Delete a blob"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            await asyncio.to_thread(blob_client.delete_blob)
            logger.info(f"Successfully deleted blob: {container_name}/{blob_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete blob: {e}")
            return False
    
    async def _ensure_container_exists(self, container_name: str):
        """Ensure that a container exists, create if it doesn't"""
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            if not await asyncio.to_thread(container_client.exists):
                await asyncio.to_thread(container_client.create_container)
                logger.info(f"Created container: {container_name}")
        except Exception as e:
            logger.error(f"Failed to ensure container exists: {e}")
            raise
    
    def get_blob_url(self, container_name: str, blob_name: str) -> str:
        """Get the URL of a blob"""
        blob_client = self.blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        return blob_client.url
