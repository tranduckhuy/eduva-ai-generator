"""
AI Worker - Main entry point and logic
"""
import asyncio
import os
import sys
import signal
from typing import Dict, Any
from dotenv import load_dotenv
import ssl

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.worker_config import WorkerConfig
from core.task_dispatcher import TaskDispatcher
from core.rabbitmq_manager import RabbitMQManager
from utils.logger import logger
import aiohttp

class AIWorker:
    """Main AI Worker class"""
    
    def __init__(self, config: WorkerConfig, session: aiohttp.ClientSession):
        """Initialize AI Worker"""
        self.config = config
        self.task_dispatcher = TaskDispatcher(config, session)
        self.rabbitmq_manager = RabbitMQManager(config, self._handle_message)
        self.is_running = False
        self.shutdown_event = asyncio.Event()
        self.semaphore = asyncio.Semaphore(config.max_concurrent_tasks or 5)
        
        logger.info(f"AI Worker {config.worker_id} initialized")
    
    async def start(self):
        """Start the AI worker"""
        try:
            logger.info(f"Starting AI Worker {self.config.worker_id}...")
            
            self._setup_signal_handlers()
            await self.rabbitmq_manager.start()
            
            self.is_running = True
            logger.info(f"AI Worker {self.config.worker_id} started successfully")
            
            # Start DLQ monitoring if enabled
            if self.config.dlq_monitoring_enabled:
                asyncio.create_task(self._monitor_dlq())
            
            await self.shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"Failed to start AI Worker: {e}")
            raise
        finally:
            await self.stop()
    
    async def _monitor_dlq(self):
        """Monitor Dead Letter Queue for alerts"""
        while self.is_running:
            try:
                dlq_info = self.rabbitmq_manager.get_dlq_info()
                message_count = dlq_info.get("message_count", 0)
                
                if message_count >= self.config.dlq_alert_threshold:
                    logger.warning(
                        f"DLQ Alert: {message_count} messages in dead letter queue "
                        f"(threshold: {self.config.dlq_alert_threshold})"
                    )
                    
                    # Optionally notify backend about DLQ issues
                    # await self._notify_dlq_alert(message_count)
                
                # Check every 60 seconds
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error monitoring DLQ: {e}")
                await asyncio.sleep(60)
    
    async def stop(self):
        """Stop the AI worker"""
        if not self.is_running:
            return
        
        logger.info(f"Stopping AI Worker {self.config.worker_id}...")
        self.is_running = False
        
        # Signal RabbitMQ manager to stop
        self.rabbitmq_manager.should_stop = True
        
        await self.rabbitmq_manager.stop()
        logger.info("AI Worker stopped")
    
    # async def _handle_message(self, message: Dict[str, Any]) -> bool:
    #     async def sem_task():
    #         async with self.semaphore:
    #             try:
    #                 logger.info(f"Processing: {message.get('jobId', 'unknown')}")
    #                 await self.task_dispatcher.dispatch_task(message)
    #             except Exception as e:
    #                 logger.error(f"Error processing message: {e}")

    #     try:
    #         asyncio.create_task(sem_task())
    #         return True
    #     except Exception as e:
    #         logger.error(f"Error dispatching task: {e}")
    #         return False

    async def _handle_message(self, message: Dict[str, Any]) -> bool:
        """Handle incoming message from RabbitMQ"""
        job_id = message.get("jobId", "unknown")
        try:
            async with self.semaphore:
                logger.info(f"Processing message: {job_id}")
                success = await self.task_dispatcher.dispatch_task(message)
                return success
        except Exception as e:
            logger.error(f"An unhandled exception occurred while processing job {job_id}: {e}", exc_info=True)
            return False

    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            # Create task to stop gracefully
            asyncio.create_task(self._graceful_shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _graceful_shutdown(self):
        """Gracefully shutdown the worker"""
        logger.info("Initiating graceful shutdown...")
        self.shutdown_event.set()
        
        # Give some time for current tasks to complete
        await asyncio.sleep(2)
        
        # Force stop if needed
        if self.is_running:
            await self.stop()
            
        # Force exit if still running
        await asyncio.sleep(1)
        logger.info("Force exiting...")
        os._exit(0)


# async def main():
#     """Run the AI worker"""
#     try:
#         worker = AIWorker(config)
#         await worker.start()
#     except KeyboardInterrupt:
#         logger.info("Stopping worker...")
#     except Exception as e:
#         logger.error(f"Error: {e}")
#         import traceback
#         traceback.print_exc()


# if __name__ == "__main__":
#     asyncio.run(main())

async def main():
    """Run the AI worker"""
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
        try:
            worker = AIWorker(config, session)
            await worker.start()
        except KeyboardInterrupt:
            logger.info("Stopping worker...")
        except Exception as e:
            logger.error(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())