"""
Backend API client for communicating with C# backend
"""
import asyncio
import json
import ssl
from typing import Dict, Any, Optional
import aiohttp
from src.utils.logger import logger
from src.config.job_status import JobStatus


class BackendApiClient:
    """Client for communicating with the C# backend API"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        Initialize backend API client
        
        Args:
            base_url: Base URL for the backend API
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        # Auto-detect SSL verification: disable for localhost, enable for production
        self.verify_ssl = not (
            'localhost' in base_url.lower() or 
            '127.0.0.1' in base_url or 
            base_url.startswith('https://192.168.') or
            base_url.startswith('https://10.') or
            base_url.startswith('https://172.')
        )
        self.session = None
        
        if not self.verify_ssl:
            logger.warning(f"SSL verification disabled for {base_url} - detected development environment")
    
    async def __aenter__(self):
        """Async context manager entry"""
        # Create SSL context based on verification setting
        ssl_context = None
        if not self.verify_ssl:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            logger.warning("SSL certificate verification disabled - only use in development!")
        
        # Create connector with SSL settings
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self.session = aiohttp.ClientSession(connector=connector)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        return headers
    
    async def _ensure_session(self):
        """Ensure session is created with proper SSL settings"""
        if not self.session:
            # Create SSL context based on verification setting
            ssl_context = None
            if not self.verify_ssl:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                logger.warning("SSL certificate verification disabled - only use in development!")
            
            # Create connector with SSL settings
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self.session = aiohttp.ClientSession(connector=connector)
    
    async def update_job_status(self, job_id: str, status_data: Dict[str, Any]) -> bool:
        """
        Update job status via PUT request to /api/ai-jobs/{id}/progress
        
        Args:
            job_id: ID of the job to update
            status_data: Status data to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        url = f"{self.base_url}/api/ai-jobs/{job_id}/progress"
        
        try:
            await self._ensure_session()
            
            logger.info(f"Updating job {job_id} progress: {status_data}")
            
            async with self.session.put(
                url,
                json=status_data,
                headers=self._get_headers()
            ) as response:
                
                if response.status == 200:
                    logger.info(f"Successfully updated job {job_id} progress")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to update job {job_id} progress. Status: {response.status}, Error: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Exception occurred while updating job {job_id} progress: {e}")
            return False
    
    async def update_job_success(self, job_id: str, status: JobStatus, **kwargs) -> bool:
        """
        Update job with success status
        
        Args:
            job_id: ID of the job to update
            status: JobStatus enum value
            **kwargs: Additional data (e.g., wordCount, contentBlobName, productBlobName)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Map to backend API structure  
        status_data = {
            "jobStatus": status.value,  # Send enum value (number)
            "wordCount": kwargs.get("wordCount"),
            "previewContent": kwargs.get("previewContent"),
            "contentBlobName": kwargs.get("contentBlobName"),
            "productBlobName": kwargs.get("productBlobName")
        }
        
        # Remove None values
        status_data = {k: v for k, v in status_data.items() if v is not None}
        
        logger.info(f"Sending status update for job {job_id}: {status_data}")
        return await self.update_job_status(job_id, status_data)
    
    async def update_job_failure(self, job_id: str, failure_reason: str) -> bool:
        """
        Update job with failure status
        
        Args:
            job_id: ID of the job to update
            failure_reason: Detailed error message
            
        Returns:
            bool: True if successful, False otherwise
        """
        from src.config.job_status import JobStatus
        
        status_data = {
            "jobStatus": JobStatus.Failed.value,  # Send enum value (number)
            "failureReason": failure_reason
        }
        
        logger.info(f"Sending failure update for job {job_id}: {status_data}")
        return await self.update_job_status(job_id, status_data)
    
    async def get_job_details(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job details from backend
        
        Args:
            job_id: ID of the job
            
        Returns:
            Dict containing job details or None if failed
        """
        url = f"{self.base_url}/api/ai-jobs/{job_id}"
        
        try:
            await self._ensure_session()
            
            async with self.session.get(
                url,
                headers=self._get_headers()
            ) as response:
                
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to get job {job_id} details. Status: {response.status}, Error: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Exception occurred while getting job {job_id} details: {e}")
            return None
    
    async def update_job_progress(self, job_id: str, percentage: int, message: str) -> bool:
        """
        Update job progress (for Phase 2 progress updates)
        
        Args:
            job_id: ID of the job to update
            percentage: Progress percentage (0-100)
            message: Progress message
            
        Returns:
            bool: True if successful, False otherwise
        """
        status_data = {
            "jobStatus": "CreatingProduct",
            "progressPercentage": percentage,
            "progressMessage": message
        }
        
        return await self.update_job_status(job_id, status_data)
