"""
Base Worker Class - Shared functionality for all workers
"""
import asyncio
import signal
import sys
from typing import Callable
from src.config.worker_config import WorkerConfig
from src.core.rabbitmq_manager import RabbitMQManager
from src.utils.logger import logger
from src.utils.temp_cleanup import cleanup_old_temp_files


class BaseWorker:
    """Base worker with graceful shutdown and common functionality"""
    
    def __init__(self, config: WorkerConfig, message_handler: Callable):
        self.config = config
        self.message_handler = message_handler
        self.rabbitmq_manager = RabbitMQManager(config, message_handler)
        self.is_running = False
        self.shutdown_event = asyncio.Event()
        
    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        if sys.platform == "win32":
            # Windows doesn't support signal handlers in asyncio
            logger.info("Windows detected - use Ctrl+C for shutdown")
            return
            
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self.trigger_shutdown)
    
    def trigger_shutdown(self):
        """Trigger graceful shutdown"""
        if not self.shutdown_event.is_set():
            logger.info("Shutdown signal received, stopping worker...")
            self.shutdown_event.set()
    
    async def start(self):
        """Start the worker"""
        if self.is_running:
            logger.warning("Worker is already running")
            return
            
        self.is_running = True
        self.setup_signal_handlers()
        
        try:
            # Clean up old temp files from previous runs
            cleanup_old_temp_files(self.config.temp_dir)
            
            # Start RabbitMQ connection
            await self.rabbitmq_manager.start()
            logger.info(f"✅ Worker started - Queue: {self.config.ai_task_queue}")
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the worker gracefully"""
        if not self.is_running:
            return
            
        logger.info("Stopping worker gracefully...")
        self.is_running = False
        
        try:
            # Stop RabbitMQ manager (this will handle running task cleanup)
            await self.rabbitmq_manager.stop()
            logger.info("✅ Worker stopped gracefully")
        except Exception as e:
            logger.error(f"Error stopping worker: {e}")
    
    async def run(self):
        """Main run method - handle KeyboardInterrupt for Windows"""
        try:
            await self.start()
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received")
            self.trigger_shutdown()
            if self.is_running:
                await self.stop()
