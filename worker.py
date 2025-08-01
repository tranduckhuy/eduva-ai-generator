"""
AI Worker - Main entry point and logic using Dependency Injection.
"""
import asyncio
import os
import sys
import signal
import traceback
from typing import Dict, Any, List
from dotenv import load_dotenv
import ssl
import aiohttp

load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.worker_config import WorkerConfig
from core.rabbitmq_manager import RabbitMQManager
from core.task_dispatcher import TaskDispatcher
from handlers.base_handler import BaseTaskHandler
from handlers.content_generation_handler import ContentGenerationHandler
from handlers.product_creation_handler import ProductCreationHandler
from models.task_messages import TaskType
from services.backend_api_client import BackendApiClient
from utils.logger import logger

class AIWorker:
    """Main AI Worker class"""
    
    def __init__(self, config: WorkerConfig, dispatcher: TaskDispatcher, rabbitmq_manager: RabbitMQManager):
        self.config = config
        self.task_dispatcher = dispatcher
        self.rabbitmq_manager = rabbitmq_manager
        self.semaphore = asyncio.Semaphore(config.max_concurrent_tasks or 2)

        logger.info(f"Semaphore initialized with {config.max_concurrent_tasks} concurrent tasks.")
        logger.info(f"Prefetch count set to {config.prefetch_count}.")

        self.is_running = False
        self.shutdown_event = asyncio.Event()
        self.background_tasks: List[asyncio.Task] = []
        logger.info(f"AI Worker {config.worker_id} initialized with injected dependencies.")
    
    async def start(self):
        """Starts the AI worker and its background tasks."""
        if self.is_running:
            logger.warning("Worker is already running.")
            return

        self.is_running = True
        self._setup_signal_handlers()

        await self.rabbitmq_manager.start()
        self.background_tasks.append(self.rabbitmq_manager.consuming_task)

        if self.config.dlq_monitoring_enabled:
            monitor_task = asyncio.create_task(self._monitor_dlq())
            self.background_tasks.append(monitor_task)

        logger.info(f"AI Worker {self.config.worker_id} started with {len(self.background_tasks)} background tasks.")
        await self.shutdown_event.wait()
    
    async def _handle_message(self, message: Dict[str, Any]) -> bool:
        """Handles an incoming message using the semaphore and dispatcher."""
        job_id = message.get("jobId", "unknown")
        try:
            async with self.semaphore:
                return await self.task_dispatcher.dispatch_task(message)
        except Exception as e:
            logger.error(f"Critical error in _handle_message for job {job_id}: {e}", exc_info=True)
            return False

    def _setup_signal_handlers(self):
        """Sets up signal handlers for graceful shutdown."""
        if sys.platform == "win32":
            logger.warning("Signal handlers are not set up on Windows. Use Ctrl+C to trigger KeyboardInterrupt.")
            return
        
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(self._graceful_shutdown(s)))

    async def _graceful_shutdown(self, sig: signal.Signals):
        """Gracefully shuts down the worker by cancelling background tasks."""
        if not self.shutdown_event.is_set():
            logger.warning(f"Received shutdown signal {sig.name}. Initiating graceful shutdown...")
            self.shutdown_event.set()

            for task in self.background_tasks:
                task.cancel()
            
            await asyncio.gather(*self.background_tasks, return_exceptions=True)

            await self.rabbitmq_manager.stop()
            
            self.is_running = False
            logger.info("Graceful shutdown complete. Exiting.")    

    async def _monitor_dlq(self):
        """Monitors the Dead Letter Queue periodically."""
        logger.info("DLQ monitor started.")
        while not self.shutdown_event.is_set():
            try:
                dlq_info = await self.rabbitmq_manager.get_dlq_info()
                message_count = dlq_info.get("message_count", 0)
                
                if message_count >= self.config.dlq_alert_threshold:
                    logger.warning(
                        f"DLQ Alert: {message_count} messages in DLQ (threshold: {self.config.dlq_alert_threshold})"
                    )
                
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                logger.info("DLQ monitor task cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in DLQ monitor: {e}", exc_info=True)
                await asyncio.sleep(60)
    
    async def stop(self):
        """
        Programmatically triggers the graceful shutdown process.
        This is a public API for stopping the worker.
        """
        logger.info("Programmatic stop called. Initiating graceful shutdown...")
        await self._graceful_shutdown(signal.SIGUSR1) 

async def main():
    """The Composition Root: Creates and wires up all application components."""
    config = WorkerConfig()
    
    verify_ssl = not ('localhost' in config.backend_api_base_url.lower() or '127.0.0.1' in config.backend_api_base_url)
    ssl_context = None
    if not verify_ssl:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        logger.warning("SSL certificate verification is DISABLED.")
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)

    async with aiohttp.ClientSession(connector=connector) as session:
        worker = None
        try:
            # 1. Create BackendApiClient with injected session and config
            backend_client = BackendApiClient(session, config.backend_api_base_url, config.backend_api_key)

            # 2. Create handlers and inject dependencies
            handlers: Dict[TaskType, BaseTaskHandler] = {
                TaskType.GENERATE_CONTENT: ContentGenerationHandler(config, backend_client),
                TaskType.CREATE_PRODUCT: ProductCreationHandler(config, backend_client)
            }

            # 3. Create TaskDispatcher and inject handlers
            dispatcher = TaskDispatcher(handlers)

            # 4. Create AIWorker and RabbitMQManager, then connect them
            worker = AIWorker(config, dispatcher, None)
            rabbitmq_manager = RabbitMQManager(config, worker._handle_message)
            worker.rabbitmq_manager = rabbitmq_manager

            await worker.start()

        except asyncio.CancelledError:
            logger.info("Main task cancelled.")
        except Exception as e:
            logger.error(f"Fatal error in main execution: {e}", exc_info=True)
            traceback.print_exc() 
        finally:
            if worker and worker.is_running:
                logger.info("Main function exiting, ensuring worker is stopped.")
                await worker._graceful_shutdown(signal.SIGABRT)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user.")