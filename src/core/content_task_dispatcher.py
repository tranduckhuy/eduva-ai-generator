"""
Content Worker Task Dispatcher - Only handles content generation
"""
from typing import Dict
from src.models.task_messages import TaskType, parse_task_message
from src.handlers.base_handler import BaseTaskHandler
from src.utils.logger import logger


class ContentTaskDispatcher:
    """Dispatcher for content-only tasks"""
    
    def __init__(self, content_handler: BaseTaskHandler):
        self.content_handler = content_handler
        logger.info("Content task dispatcher initialized")
    
    async def dispatch_task(self, message_body: Dict) -> bool:
        """Dispatch only content generation tasks"""
        try:
            task_message = parse_task_message(message_body)
            
            # Only handle content generation
            if task_message.taskType != TaskType.GENERATE_CONTENT:
                logger.warning(f"Ignoring non-content task: {task_message.taskType}")
                return True
            
            logger.info(f"Processing content task for job {task_message.jobId}")
            success = await self.content_handler.process(task_message)
            
            if success:
                logger.info(f"✅ Content task for job {task_message.jobId} completed")
            else:
                logger.error(f"❌ Content task for job {task_message.jobId} failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Error dispatching task: {e}")
            return False
