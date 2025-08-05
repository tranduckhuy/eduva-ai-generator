"""
Base task handler for AI processing tasks
"""
import os
import json
import tempfile
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from src.models.task_messages import TaskMessage
from src.services.azure_blob_service import AzureBlobService
from src.services.backend_api_client import BackendApiClient
from src.config.worker_config import WorkerConfig
from src.utils.logger import logger
from src.config.job_status import JobStatus


class BaseTaskHandler(ABC):

    def __init__(self, config: WorkerConfig, backend_client: BackendApiClient):
        """Initialize base task handler with shared clients."""
        self.config = config
        self.backend_client = backend_client
        self.azure_service = AzureBlobService(config.azure_storage_connection_string)
    
    @abstractmethod
    async def process(self, message: TaskMessage) -> bool:
        """
        Process the task message
        
        Args:
            message: Task message to process
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    async def download_source_file(self, blob_name: str, local_path: Optional[str] = None) -> str:
        try:
            # Use input container for source files
            container_name = self.config.azure_input_container
            
            if local_path is None:
                # Create temp file with proper extension
                file_extension = os.path.splitext(blob_name)[1] or '.tmp'
                with tempfile.NamedTemporaryFile(
                    suffix=file_extension, 
                    delete=False,
                    dir=self.config.temp_dir
                ) as temp_file:
                    local_path = temp_file.name
            
            local_path = await self.azure_service.download_file(
                container_name, 
                blob_name, 
                local_path
            )
            
            logger.info(f"Downloaded source file: {blob_name} -> {local_path}")
            return local_path
            
        except Exception as e:
            logger.error(f"Failed to download source file {blob_name}: {e}")
            raise
    
    async def download_multiple_source_files(self, blob_names: List[str]) -> List[str]:
        try:
            local_paths = []
            
            for blob_name in blob_names:
                local_path = await self.download_source_file(blob_name)
                local_paths.append(local_path)
            
            logger.info(f"Downloaded {len(local_paths)} source files")
            return local_paths
            
        except Exception as e:
            logger.error(f"Failed to download multiple source files: {e}")
            raise

    async def upload_content_file(self, local_path: str, blob_name: str) -> str:
        try:
            # Use temp container for intermediate content (JSON)
            container_name = self.config.azure_input_container
            
            # Determine content type based on file extension
            file_extension = os.path.splitext(local_path)[1].lower()
            content_type_map = {
                '.json': 'application/json',
                '.txt': 'text/plain',
                '.pdf': 'application/pdf',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.mp3': 'audio/mpeg',
                '.mp4': 'video/mp4'
            }
            content_type = content_type_map.get(file_extension, 'application/octet-stream')
            
            blob_url = await self.azure_service.upload_file(
                container_name,
                blob_name,
                local_path,
                content_type
            )
            
            logger.info(f"Uploaded content file to temp storage: {local_path} -> {blob_name}")
            return blob_url
            
        except Exception as e:
            logger.error(f"Failed to upload content file {local_path}: {e}")
            raise
    
    async def upload_product_file(self, local_path: str, blob_name: str) -> str:
        try:
            # Use output container for final products (video/audio)
            container_name = self.config.azure_output_container
            
            # Determine content type based on file extension
            file_extension = os.path.splitext(local_path)[1].lower()
            content_type_map = {
                '.mp4': 'video/mp4',
                '.mp3': 'audio/mpeg',
                '.avi': 'video/x-msvideo',
                '.mov': 'video/quicktime'
            }
            content_type = content_type_map.get(file_extension, 'application/octet-stream')
            
            blob_url = await self.azure_service.upload_file(
                container_name,
                blob_name,
                local_path,
                content_type
            )
            
            logger.info(f"Uploaded final product: {local_path} -> {blob_name}")
            return blob_url
            
        except Exception as e:
            logger.error(f"Failed to upload product file {local_path}: {e}")
            raise
    
    async def upload_json_content(self, content: Dict[str, Any], blob_name: str) -> str:
        try:
            # Use temp container for JSON content
            container_name = self.config.azure_input_container
            
            json_content = json.dumps(content, ensure_ascii=False, indent=2)
            content_bytes = json_content.encode('utf-8')
            
            blob_url = await self.azure_service.upload_content(
                container_name,
                blob_name,
                content_bytes,
                'application/json'
            )
            
            logger.info(f"Uploaded JSON content to temp storage: {blob_name}")
            return blob_url
            
        except Exception as e:
            logger.error(f"Failed to upload JSON content {blob_name}: {e}")
            raise
    
    async def download_json_content(self, blob_name: str) -> Dict[str, Any]:
        try:
            # Download from temp container
            container_name = self.config.azure_input_container
            
            # Download to temp file
            local_path = await self.azure_service.download_file(
                container_name,
                blob_name
            )
            
            # Read and parse JSON
            with open(local_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            # Clean up temp file
            os.unlink(local_path)
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to download JSON content {blob_name}: {e}")
            raise

    async def delete_blob(self, container_name: str, blob_name: str) -> bool:
        try:
            return await self.azure_service.delete_blob(container_name, blob_name)
        except Exception as e:
            logger.error(f"Failed to delete blob {blob_name}: {e}")
            return False

    
    async def notify_success(self, job_id: str, status: JobStatus, **kwargs) -> bool:
        try:
            # async with self.backend_client:
            #     success = await self.backend_client.update_job_success(
            #         job_id, status, **kwargs
            #     )
            success = await self.backend_client.update_job_success(
                job_id, status, **kwargs
            )
            
            if success:
                logger.info(f"Successfully notified backend of job {job_id} success")
            else:
                logger.warning(f"Failed to notify backend of job {job_id} success")
            
            return success
            
        except Exception as e:
            logger.error(f"Exception occurred while notifying success for job {job_id}: {e}")
            return False
    
    async def notify_failure(self, job_id: str, failure_reason: str) -> bool:
        try:
            # async with self.backend_client:
            #     success = await self.backend_client.update_job_failure(
            #         job_id, failure_reason
            #     )
            success = await self.backend_client.update_job_failure(
                    job_id, failure_reason
            )
            
            if success:
                logger.info(f"Successfully notified backend of job {job_id} failure")
            else:
                logger.warning(f"Failed to notify backend of job {job_id} failure")
            
            return success
            
        except Exception as e:
            logger.error(f"Exception occurred while notifying failure for job {job_id}: {e}")
            return False
    
    def cleanup_temp_files(self, *file_paths):
        """Clean up temporary files"""
        for file_path in file_paths:
            try:
                if file_path and os.path.exists(file_path):
                    os.unlink(file_path)
                    logger.debug(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {file_path}: {e}")
    
    def count_words(self, text: str) -> int:
        """Count words in text"""
        if not text:
            return 0
        return len(text.split())
