import asyncio
import json
from typing import Callable, Dict, Any
import aio_pika
from src.config.worker_config import WorkerConfig
from src.utils.logger import logger

class RabbitMQManager:
    """
    Manager for RabbitMQ using the async-native aio-pika library.
    It handles connections, message consumption, and DLQ/retry logic gracefully.
    """
    
    def __init__(self, config: WorkerConfig, message_handler: Callable):
        self.config = config
        self.message_handler = message_handler
        self.connection = None
        self.consuming_task = None
        self.running_tasks = set()  # Track running message processing tasks
        logger.info(f"aio-pika RabbitMQ manager initialized for queue: {config.ai_task_queue}")

    async def start(self):
        """Connects to RabbitMQ and starts the message consuming task."""
        try:
            self.connection = await aio_pika.connect_robust(
                self.config.rabbitmq_uri, 
                timeout=30
            )
            
            self.consuming_task = asyncio.create_task(self._consume())
            logger.info("RabbitMQ consumer has been started.")

        except Exception as e:
            logger.error(f"Failed to start RabbitMQ connection: {e}", exc_info=True)
            raise

    async def _consume(self):
        """The main message consuming loop."""
        async with self.connection:
            channel = await self.connection.channel()
            await channel.set_qos(prefetch_count=self.config.prefetch_count or 1)
            print(f"Setting prefetch count to {self.config.prefetch_count}")
            dlq_exchange = await channel.declare_exchange(self.config.dlq_exchange, aio_pika.ExchangeType.DIRECT, durable=True)
            dlq_queue = await channel.declare_queue(self.config.dlq_queue, durable=True)
            await dlq_queue.bind(dlq_exchange, self.config.dlq_routing_key)

            queue = await channel.declare_queue(
                name=self.config.ai_task_queue,
                durable=True,
                arguments={
                    'x-dead-letter-exchange': self.config.dlq_exchange,
                    'x-dead-letter-routing-key': self.config.dlq_routing_key
                }
            )
            await queue.bind(self.config.main_exchange, self.config.routing_key)

            logger.info("Consumer is waiting for messages.")
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    # Create task and track it
                    task = asyncio.create_task(self._process_message_safely(message))
                    self.running_tasks.add(task)
                    # Remove task when done
                    task.add_done_callback(lambda t: self.running_tasks.discard(t))
    
    async def _process_message_safely(self, message: aio_pika.IncomingMessage):
        """
        A safe wrapper to process a single message and handle its lifecycle (ack/nack).
        This replaces all the _process_message, _handle_success, _handle_failure logic.
        """
        job_id = "unknown"
        try:
            async with message.process(requeue=False, ignore_processed=True):
                data = json.loads(message.body.decode())
                job_id = data.get('jobId', 'unknown')
                
                retry_count = message.headers.get('x-retry-count', 0)
                if retry_count >= self.config.max_retries:
                    logger.error(f"Message {job_id} reached max retries ({retry_count}). Sending to DLQ.")
                    raise RuntimeError("Max retries exceeded")

                logger.info(f"🔄 Processing message {job_id} (retry: {retry_count})")
                success = await self.message_handler(data)
                
                if not success:
                    logger.warning(f"⚠️ Handler failed for job {job_id}. Retrying...")
                    await self._retry_message(message, retry_count + 1)
                else:
                    logger.info(f"✅ Message {job_id} processed successfully.")
        
        except asyncio.CancelledError:
            logger.info(f"Task for job {job_id} was cancelled during shutdown")
            return
            
        except Exception as e:
            logger.error(f"🔥 Unhandled exception for job {job_id}: {e}. Message will be rejected.", exc_info=True)

    async def _retry_message(self, original_message: aio_pika.IncomingMessage, next_retry_count: int):
        """Publishes a new message to the main exchange to retry."""
        async with self.connection.channel() as channel:
            exchange = await channel.get_exchange(self.config.main_exchange)
            await exchange.publish(
                aio_pika.Message(
                    body=original_message.body,
                    headers={'x-retry-count': next_retry_count},
                    delivery_mode=original_message.delivery_mode
                ),
                routing_key=self.config.routing_key
            )

    async def stop(self):
        """Stops the RabbitMQ consumer gracefully."""
        logger.info("Stopping RabbitMQ consumer...")
        
        # Cancel consuming task first
        if self.consuming_task:
            self.consuming_task.cancel()
            try:
                await self.consuming_task
            except asyncio.CancelledError:
                logger.info("Consuming task cancelled.")
        
        # Cancel running tasks with simple timeout
        if self.running_tasks:
            logger.info(f"Cancelling {len(self.running_tasks)} running tasks...")
            for task in list(self.running_tasks):
                task.cancel()
            
            # Simple wait with timeout
            try:
                await asyncio.wait_for(asyncio.sleep(3), timeout=5.0)
            except asyncio.TimeoutError:
                pass
            logger.info("Running tasks cancelled.")
        
        # Close connection
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        logger.info("RabbitMQ connection closed.")

    async def reprocess_dlq_messages(self, limit: int = 10) -> int:
        """Reprocesses messages from the DLQ back to the main queue."""
        reprocessed_count = 0
        async with self.connection.channel() as channel:
            dlq_queue = await channel.get_queue(self.config.dlq_queue)
            main_exchange = await channel.get_exchange(self.config.main_exchange)

            while reprocessed_count < limit:
                try:
                    message = await dlq_queue.get(timeout=1, fail=False)
                    if not message: break
                    
                    async with message.process(requeue=False):
                        logger.info(f"Reprocessing message from DLQ with body: {message.body.decode()}")
                        await main_exchange.publish(
                            aio_pika.Message(body=message.body, headers={}),
                            routing_key=self.config.routing_key
                        )
                        reprocessed_count += 1
                except asyncio.TimeoutError:
                    break
        
        logger.info(f"Total messages reprocessed from DLQ: {reprocessed_count}")
        return reprocessed_count
    
    async def get_dlq_info(self) -> Dict[str, Any]:
        """Gets information about the dead-letter queue."""
        if not self.connection or self.connection.is_closed:
            return {"message_count": 0}
        try:
            async with self.connection.channel() as channel:
                dlq_queue = await channel.get_queue(self.config.dlq_queue, ensure=True)
                return {"message_count": dlq_queue.declaration_result.message_count}
        except Exception as e:
            logger.warning(f"Could not get DLQ info: {e}")
            return {}