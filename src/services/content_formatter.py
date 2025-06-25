"""
Content formatting utilities for video generation
"""
from typing import List
import logging

logger = logging.getLogger(__name__)

class ContentFormatter:
    """Helper class for formatting content arrays and extracting search context"""
    
    @staticmethod
    def format_content_for_display(content: List[str]) -> str:
        """Format content array for display with proper bullet points"""
        if not content:
            return ""
        
        formatted_lines = []
        for item in content[:8]:  # Increased limit to 8 items
            if item.strip():
                # Clean up the content item
                clean_item = item.strip()
                # Add bullet point if not already present
                if not clean_item.startswith('•') and not clean_item.startswith('-'):
                    clean_item = f"• {clean_item}"
                formatted_lines.append(clean_item)
        
        return '\n'.join(formatted_lines)
    
    @staticmethod
    def get_content_context_for_search(content: List[str]) -> str:
        """Extract key terms from content array for image search context"""
        if not content:
            return ""
        
        # Join all content and extract key terms
        full_content = ' '.join(content)
        # Remove common words and keep meaningful terms
        words = full_content.lower().split()
        
        # Filter out common words (enhanced list)
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'a', 'an', 'this', 'that',
            'these', 'those', 'it', 'its', 'they', 'them', 'their', 'we', 'our', 'you', 'your',
            'he', 'his', 'she', 'her', 'i', 'my', 'me', 'us', 'him', 'not', 'no', 'yes', 'if',
            'when', 'where', 'how', 'what', 'who', 'why', 'which', 'than', 'then', 'now', 'here',
            'there', 'very', 'much', 'many', 'more', 'most', 'some', 'any', 'all', 'each', 'every',
            'về', 'của', 'và', 'với', 'trong', 'trên', 'dưới', 'từ', 'đến', 'cho', 'bởi', 'qua',
            'là', 'được', 'có', 'không', 'này', 'đó', 'các', 'một', 'những', 'sẽ', 'đã', 'đang'
        }
        
        meaningful_words = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Return first 4 meaningful words for better context
        return ' '.join(meaningful_words[:4])
    
    @staticmethod
    def extract_keywords_from_content(content: List[str], max_keywords: int = 5) -> List[str]:
        """Extract potential keywords from content for image search"""
        if not content:
            return []
        
        # Join all content
        full_content = ' '.join(content).lower()
        
        # Split into words and filter
        words = full_content.split()
        
        # Filter out stop words and short words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'a', 'an', 'this', 'that',
            'về', 'của', 'và', 'với', 'trong', 'trên', 'dưới', 'từ', 'đến', 'cho', 'bởi', 'qua',
            'là', 'được', 'có', 'không', 'này', 'đó', 'các', 'một', 'những', 'sẽ', 'đã', 'đang'
        }
        
        # Extract meaningful words
        meaningful_words = []
        for word in words:
            # Clean word (remove punctuation)
            clean_word = ''.join(c for c in word if c.isalnum())
            if (len(clean_word) > 3 and 
                clean_word not in stop_words and 
                clean_word not in meaningful_words):
                meaningful_words.append(clean_word)
        
        return meaningful_words[:max_keywords]
    
    @staticmethod
    def calculate_content_display_duration(tts_script: str, base_duration: float = 3.0) -> float:
        """Calculate appropriate display duration based on content length"""
        if not tts_script:
            return base_duration
        
        # Calculate total content length
        total_chars = len(tts_script)
        
        # Base reading speed: ~200 characters per minute = ~3.33 chars per second
        # Add buffer time for comprehension
        reading_time = total_chars / 3.33
        
        # Minimum 4 seconds, maximum 12 seconds per slide
        duration = max(4.0, min(12.0, reading_time + 2.0))
        
        logger.debug(f"Calculated content duration: {duration:.1f}s for {total_chars} characters")
        return duration
