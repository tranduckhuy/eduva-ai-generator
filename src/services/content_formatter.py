"""
Content formatting utilities for video generation
"""
from typing import List
from src.utils.logger import logger

class ContentFormatter:
    """Helper class for formatting content for video slides"""
    @staticmethod
    def calculate_content_display_duration(tts_script: str, base_duration: float = 5.0) -> float:
        """Calculate appropriate display duration based on content length - INCREASED for better readability"""
        if not tts_script:
            return base_duration
        
        # Calculate total content length
        total_chars = len(tts_script)
        
        reading_time = total_chars / 2.5
        
        duration = max(8.0, min(18.0, reading_time + 4.0))  # More buffer time
        
        logger.debug(f"Calculated content duration: {duration:.1f}s for {total_chars} characters")
        return duration
