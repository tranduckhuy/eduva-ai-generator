"""
Message models for task processing
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum

class TaskType(Enum):
    """Types of tasks that can be processed"""
    GENERATE_CONTENT = 0
    CREATE_PRODUCT = 1


class JobType(Enum):
    """Types of jobs - matches C# AIServiceType enum"""
    AUDIO_LESSON = 0  # GenAudio
    VIDEO_LESSON = 1  # GenVideo


@dataclass
class TaskMessage:
    """Base task message structure"""
    jobId: str
    taskType: TaskType  # Changed from str to TaskType enum
    
    def __post_init__(self):
        """Validate task message"""
        if not isinstance(self.taskType, TaskType):
            raise ValueError(f"Invalid taskType: {self.taskType}")


@dataclass
class GenerateContentMessage(TaskMessage):
    """Message for generate_content task"""
    topic: str
    sourceBlobNames: List[str]
    
    def __post_init__(self):
        super().__post_init__()
        if self.taskType != TaskType.GENERATE_CONTENT:
            raise ValueError("taskType must be 'generate_content' for GenerateContentMessage")
        
        if not self.topic:
            raise ValueError("topic is required for GenerateContentMessage")
        
        if not self.sourceBlobNames or len(self.sourceBlobNames) == 0:
            raise ValueError("sourceBlobNames must contain at least one file")


@dataclass
class CreateProductMessage(TaskMessage):
    """Message for create_product task"""
    contentBlobName: str
    jobType: JobType  # Required for product creation to know video/audio
    voiceConfig: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.taskType != TaskType.CREATE_PRODUCT:
            raise ValueError("taskType must be 'create_product' for CreateProductMessage")
        
        if not isinstance(self.jobType, JobType):
            raise ValueError(f"Invalid jobType: {self.jobType}")
        
        if not self.contentBlobName:
            raise ValueError("contentBlobName is required for CreateProductMessage")


def parse_task_message(message_body: Dict[str, Any]) -> TaskMessage:
    """
    Parse raw message body into appropriate TaskMessage object
    
    Args:
        message_body: Raw message body from RabbitMQ
        
    Returns:
        TaskMessage: Parsed message object
        
    Raises:
        ValueError: If message format is invalid
    """
    task_type_value = message_body.get("taskType")
    
    if task_type_value is None:
        raise ValueError("Missing 'taskType' in message")
    
    # Convert taskType to enum - handle both int and string
    if isinstance(task_type_value, int):
        try:
            task_type = TaskType(task_type_value)
        except ValueError:
            raise ValueError(f"Invalid taskType: {task_type_value}")
    elif isinstance(task_type_value, str):
        try:
            # Try to parse as int first
            task_type = TaskType(int(task_type_value))
        except ValueError:
            # Try as enum name
            try:
                task_type = TaskType[task_type_value.upper()]
            except KeyError:
                raise ValueError(f"Invalid taskType: {task_type_value}")
    else:
        raise ValueError(f"Invalid taskType type: {type(task_type_value)}")
    
    if task_type == TaskType.GENERATE_CONTENT:
        return GenerateContentMessage(
            taskType=task_type,
            jobId=message_body["jobId"],
            topic=message_body["topic"],
            sourceBlobNames=message_body["sourceBlobNames"]
        )
    
    elif task_type == TaskType.CREATE_PRODUCT:
        # Parse jobType - handle integer values from C# backend
        job_type_value = message_body.get("jobType")
        if job_type_value is None:
            raise ValueError("jobType is required for CREATE_PRODUCT tasks")
        
        # Handle integer values from C# backend
        if isinstance(job_type_value, int):
            try:
                job_type = JobType(job_type_value)
            except ValueError:
                raise ValueError(f"Invalid jobType: {job_type_value}")
        elif isinstance(job_type_value, str):
            # Try to parse as int first (in case it's a string representation)
            try:
                job_type = JobType(int(job_type_value))
            except (ValueError, TypeError):
                # If that fails, try as string enum name
                try:
                    job_type = JobType[job_type_value.upper()]
                except KeyError:
                    raise ValueError(f"Invalid jobType: {job_type_value}")
        elif isinstance(job_type_value, JobType):
            job_type = job_type_value
        else:
            raise ValueError(f"Invalid jobType: {job_type_value}")
        
        return CreateProductMessage(
            taskType=task_type,
            jobId=message_body["jobId"],
            jobType=job_type,
            contentBlobName=message_body["contentBlobName"],
            voiceConfig=message_body.get("voiceConfig")
        )
    
    else:
        raise ValueError(f"Unknown taskType: {task_type}")
