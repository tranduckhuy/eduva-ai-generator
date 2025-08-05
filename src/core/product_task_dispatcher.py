"""
Product Worker Task Dispatcher - Only handles product creation
"""
from typing import Dict
from src.models.task_messages import TaskType, parse_task_message
from src.handlers.base_handler import BaseTaskHandler
from src.utils.logger import logger


class ProductTaskDispatcher:
    """Dispatcher for product-only tasks"""
    
    def __init__(self, product_handler: BaseTaskHandler):
        self.product_handler = product_handler
        logger.info("Product task dispatcher initialized")
    
    async def dispatch_task(self, message_body: Dict) -> bool:
        """Dispatch only product creation tasks"""
        try:
            task_message = parse_task_message(message_body)
            
            # Only handle product creation
            if task_message.taskType != TaskType.CREATE_PRODUCT:
                logger.warning(f"Ignoring non-product task: {task_message.taskType}")
                return True  # Acknowledge but don't process
            
            logger.info(f"Processing product task for job {task_message.jobId}")
            success = await self.product_handler.process(task_message)
            
            if success:
                logger.info(f"✅ Product task for job {task_message.jobId} completed")
            else:
                logger.error(f"❌ Product task for job {task_message.jobId} failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Error dispatching task: {e}")
            return False
