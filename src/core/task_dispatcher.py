"""
Task dispatcher for routing messages to appropriate handlers
"""
from typing import Dict, Type
from src.models.task_messages import TaskMessage, TaskType, parse_task_message
from src.handlers.base_handler import BaseTaskHandler
from src.handlers.content_generation_handler import ContentGenerationHandler
from src.handlers.product_creation_handler import ProductCreationHandler
from src.config.worker_config import WorkerConfig
from src.utils.logger import logger


class TaskDispatcher:
    """Dispatcher for routing tasks to appropriate handlers"""
    
    def __init__(self, config: WorkerConfig):
        """Initialize task dispatcher"""
        self.config = config
        
        # Initialize handlers
        self.handlers: Dict[TaskType, BaseTaskHandler] = {
            TaskType.GENERATE_CONTENT: ContentGenerationHandler(config),
            TaskType.CREATE_PRODUCT: ProductCreationHandler(config)
        }
        
        logger.info(f"Task dispatcher initialized with {len(self.handlers)} handlers")
    
    async def dispatch_task(self, message_body: Dict) -> bool:
        """Dispatch task to appropriate handler"""
        try:
            task_message = parse_task_message(message_body)
            logger.info(f"Dispatching task: {task_message.taskType} for job {task_message.jobId}")
            
            handler = self.handlers.get(task_message.taskType)
            if not handler:
                raise ValueError(f"No handler found for task type: {task_message.taskType}")
            
            success = await handler.process(task_message)
            
            if success:
                logger.info(f"Task {task_message.taskType} for job {task_message.jobId} completed successfully")
            else:
                logger.error(f"Task {task_message.taskType} for job {task_message.jobId} failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to dispatch task: {e}")
            
            # Try to extract job_id for failure notification
            try:
                job_id = message_body.get("jobId")
                if job_id:
                    handler = next(iter(self.handlers.values()))
                    await handler.notify_failure(job_id, f"Task dispatch failed: {str(e)}")
            except Exception as notify_error:
                logger.error(f"Failed to notify backend of dispatch failure: {notify_error}")
            
            return False
    
    async def health_check(self) -> Dict[str, bool]:
        """Perform health check on all handlers"""
        health_status = {}
        
        for task_type, handler in self.handlers.items():
            try:
                health_status[task_type] = handler is not None
            except Exception as e:
                logger.error(f"Health check failed for {task_type}: {e}")
                health_status[task_type] = False
        
        return health_status
