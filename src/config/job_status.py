"""
Constants for job status matching backend enum
"""
from enum import Enum


class JobStatus(Enum):
    """
    Job processing status enum matching backend JobStatus enum exactly
    """
    Processing = 1
    ContentGenerated = 2
    CreatingProduct = 3
    Completed = 4
    Failed = 5
    Expired = 6
    Cancelled = 7
