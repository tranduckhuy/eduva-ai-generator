"""
Content formatting utilities for video generation
"""
from typing import List
import logging

logger = logging.getLogger(__name__)

class ContentFormatter:
    """Helper class for formatting content for video slides"""
    @staticmethod
    def calculate_content_display_duration(tts_script: str, base_duration: float = 5.0) -> float:
        """Calculate appropriate display duration based on content length - INCREASED for better readability"""
        if not tts_script:
            return base_duration
        
        # Calculate total content length
        total_chars = len(tts_script)
        
        # Slower reading speed for better comprehension: ~150 characters per minute = ~2.5 chars per second
        # Add more buffer time for Vietnamese text and comprehension
        reading_time = total_chars / 2.5
        
        # Increased minimum to 8 seconds, maximum 18 seconds per slide for comfortable reading
        duration = max(8.0, min(18.0, reading_time + 4.0))  # More buffer time
        
        logger.debug(f"Calculated content duration: {duration:.1f}s for {total_chars} characters")
        return duration
