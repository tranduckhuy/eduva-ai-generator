"""
Module for cleaning slide content from markdown and special characters
"""
import re
from typing import Dict, List, Any
from src.utils.logger import logger


def clean_all_slide_content(slide_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean all slide content from markdown formatting and special characters
    Specifically designed for TTS and clean presentation
    """
    if not slide_data:
        return slide_data
    
    try:
        # Clean lesson_info
        if "lesson_info" in slide_data:
            lesson_info = slide_data["lesson_info"]
            if "title" in lesson_info:
                lesson_info["title"] = clean_markdown_text(lesson_info["title"])
        
        # Clean all slides
        if "slides" in slide_data:
            for slide in slide_data["slides"]:
                # Clean title
                if "title" in slide:
                    slide["title"] = clean_markdown_text(slide["title"])
                
                # Clean content array
                if "content" in slide and isinstance(slide["content"], list):
                    slide["content"] = [clean_markdown_text(str(item)) for item in slide["content"]]
                
                # Clean TTS script - most important
                if "tts_script" in slide:
                    slide["tts_script"] = clean_tts_script(slide["tts_script"])
                
                # Clean source references
                if "source_references" in slide and isinstance(slide["source_references"], list):
                    slide["source_references"] = [clean_markdown_text(str(ref)) for ref in slide["source_references"]]
                
                # Clean content_extracted_from
                if "content_extracted_from" in slide:
                    slide["content_extracted_from"] = clean_markdown_text(slide["content_extracted_from"])
        
        logger.info("Successfully cleaned all slide content from markdown and special characters")
        return slide_data
        
    except Exception as e:
        logger.error(f"Error cleaning slide content: {e}")
        return slide_data


def clean_markdown_text(text: str) -> str:
    """Remove markdown formatting from text"""
    if not text:
        return ""
    
    # Remove markdown bold/italic
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold** -> bold
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic* -> italic
    text = re.sub(r'__([^_]+)__', r'\1', text)      # __bold__ -> bold
    text = re.sub(r'_([^_]+)_', r'\1', text)        # _italic_ -> italic
    
    # Remove markdown headers
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)  # # Header -> Header
    
    # Remove markdown lists
    text = re.sub(r'^\s*[-*+]\s*', '', text, flags=re.MULTILINE)  # - item -> item
    text = re.sub(r'^\s*\d+\.\s*', '', text, flags=re.MULTILINE)  # 1. item -> item
    
    # Remove markdown links
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # [text](url) -> text
    
    # Remove markdown code
    text = re.sub(r'`([^`]+)`', r'\1', text)  # `code` -> code
    text = re.sub(r'```[^`]*```', '', text)   # ```code block``` -> (remove)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def clean_tts_script(script: str) -> str:
    """Clean TTS script from unwanted characters and formatting for optimal TTS"""
    if not script:
        return ""
    
    # First clean markdown
    script = clean_markdown_text(script)
    
    # Remove newlines and tabs that interfere with TTS
    script = re.sub(r'[\n\r\t]+', ' ', script)
    
    # Remove excessive whitespace
    script = re.sub(r'\s+', ' ', script)
    
    # Remove special characters that might interfere with TTS
    script = re.sub(r'[_*#`@$%^&(){}[\]|\\<>]', '', script)
    
    # Fix punctuation spacing for natural TTS flow
    script = re.sub(r'\s*\.\s*', '. ', script)
    script = re.sub(r'\s*,\s*', ', ', script)
    script = re.sub(r'\s*\?\s*', '? ', script)
    script = re.sub(r'\s*!\s*', '! ', script)
    script = re.sub(r'\s*:\s*', ': ', script)
    script = re.sub(r'\s*;\s*', '; ', script)
    
    # Remove multiple spaces
    script = re.sub(r'\s+', ' ', script)
    
    # Ensure script ends with proper punctuation
    script = script.strip()
    if script and not script[-1] in '.!?':
        script += '.'
    
    return script


def validate_clean_content(slide_data: Dict[str, Any]) -> bool:
    """
    Validate that slide content is properly cleaned
    Returns True if content is clean, False if markdown/special chars found
    """
    if not slide_data:
        return True
    
    try:
        markdown_patterns = [
            r'\*\*[^*]+\*\*',  # **bold**
            r'\*[^*]+\*',      # *italic*
            r'__[^_]+__',      # __bold__
            r'_[^_]+_',        # _italic_
            r'^#{1,6}\s',      # # headers
            r'```[^`]*```',    # code blocks
            r'`[^`]+`',        # inline code
        ]
        
        # Check lesson_info title
        if "lesson_info" in slide_data and "title" in slide_data["lesson_info"]:
            title = slide_data["lesson_info"]["title"]
            for pattern in markdown_patterns:
                if re.search(pattern, title, re.MULTILINE):
                    logger.warning(f"Markdown found in lesson title: {title}")
                    return False
        
        # Check slides
        if "slides" in slide_data:
            for i, slide in enumerate(slide_data["slides"]):
                # Check slide title
                if "title" in slide:
                    for pattern in markdown_patterns:
                        if re.search(pattern, slide["title"], re.MULTILINE):
                            logger.warning(f"Markdown found in slide {i+1} title: {slide['title']}")
                            return False
                
                # Check slide content
                if "content" in slide and isinstance(slide["content"], list):
                    for j, content_item in enumerate(slide["content"]):
                        for pattern in markdown_patterns:
                            if re.search(pattern, str(content_item), re.MULTILINE):
                                logger.warning(f"Markdown found in slide {i+1} content {j+1}: {content_item}")
                                return False
                
                # Check TTS script for problematic characters
                if "tts_script" in slide:
                    tts = slide["tts_script"]
                    if re.search(r'[\n\r\t]', tts):
                        logger.warning(f"Newline/tab characters found in slide {i+1} TTS script")
                        return False
                    for pattern in markdown_patterns:
                        if re.search(pattern, tts, re.MULTILINE):
                            logger.warning(f"Markdown found in slide {i+1} TTS script")
                            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating clean content: {e}")
        return False