"""
Simple temp cleanup utility
"""
import os
import shutil
import time
from src.utils.logger import logger


def cleanup_old_temp_files(temp_base_dir: str, max_age_hours: int = 24):
    """
    Clean up temp files older than max_age_hours
    """
    if not os.path.exists(temp_base_dir):
        return
    
    current_time = time.time()
    cutoff_time = current_time - (max_age_hours * 3600)
    
    try:
        for item in os.listdir(temp_base_dir):
            item_path = os.path.join(temp_base_dir, item)
            
            if os.path.isdir(item_path):
                # Check directory modification time
                if os.path.getmtime(item_path) < cutoff_time:
                    try:
                        shutil.rmtree(item_path)
                        logger.info(f"Cleaned up old temp directory: {item}")
                    except Exception as e:
                        logger.warning(f"Could not cleanup {item_path}: {e}")
                        
    except Exception as e:
        logger.warning(f"Error cleaning temp directory: {e}")


def force_cleanup_workspace(workspace_dir: str):
    """
    Force cleanup workspace directory with retry
    """
    if not os.path.exists(workspace_dir):
        return
        
    max_retries = 3
    for attempt in range(max_retries):
        try:
            shutil.rmtree(workspace_dir)
            logger.info(f"Cleaned up workspace: {workspace_dir}")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Cleanup attempt {attempt + 1} failed, retrying: {e}")
                time.sleep(1)
            else:
                logger.error(f"Failed to cleanup workspace after {max_retries} attempts: {e}")
