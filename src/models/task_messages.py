"""
Message models for task processing
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum


class TaskType(str, Enum):
    """Types of tasks that can be processed"""
    GENERATE_CONTENT = "generate_content"
    CREATE_PRODUCT = "create_product"


class JobType(Enum):
    """Types of jobs - matches C# AIServiceType enum"""
    AUDIO_LESSON = 0  # GenAudio
    VIDEO_LESSON = 1  # GenVideo


@dataclass
class TaskMessage:
    """Base task message structure"""
    jobId: str
    taskType: str
    
    def __post_init__(self):
        """Validate task message"""
        if self.taskType not in [TaskType.GENERATE_CONTENT, TaskType.CREATE_PRODUCT]:
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
    task_type = message_body.get("taskType")
    
    if not task_type:
        raise ValueError("Missing 'taskType' in message")
    
    if task_type == TaskType.GENERATE_CONTENT:
        return GenerateContentMessage(
            taskType=message_body["taskType"],
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
            taskType=message_body["taskType"],
            jobId=message_body["jobId"],
            jobType=job_type,
            contentBlobName=message_body["contentBlobName"],
            voiceConfig=message_body.get("voiceConfig")
        )
    
    else:
        raise ValueError(f"Unknown taskType: {task_type}")


# Example message structures for documentation

EXAMPLE_GENERATE_CONTENT_MESSAGE = {
    "taskType": "generate_content",
    "jobId": "12345",
    "topic": "Introduction to Python",
    "sourceBlobNames": ["source_document.pdf", "additional_notes.docx"]
}

EXAMPLE_CREATE_PRODUCT_MESSAGE = {
    "taskType": "create_product",
    "jobId": "12345",
    "jobType": 1,  # 0 for audio, 1 for video (matches C# AIServiceType enum)
    "contentBlobName": "lesson_content.json",
    "voiceConfig": {
        "language_code": "vi-VN",
        "name": "vi-VN-Neural2-A",
        "speaking_rate": 1.0
    }
}
