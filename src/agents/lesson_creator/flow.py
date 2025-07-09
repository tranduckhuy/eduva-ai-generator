import os
from src.utils.logger import logger
from .func import create_slide_data
from .prompt import create_messages_for_llm

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL")

async def run_slide_creator(topic: str, uploaded_files_content: str = None, model_name: str = DEFAULT_MODEL):
    """Simplified slide creator focused on topic and file upload only"""
    try:
        logger.info(f"Creating slides for topic: {topic}")
        
        # Step 1: Build prompt messages (no vector store query needed)
        prompt_messages = create_messages_for_llm(
            topic=topic,
            uploaded_files_content=uploaded_files_content
        )

        # Step 2: Generate slides with LLM
        from src.config.llm import get_llm
        llm = get_llm(model_name)
        logger.info(f"Generating slides with {model_name}...")
        
        response = await llm.ainvoke(prompt_messages)
        
        # Step 3: Parse response and create slide data
        slide_data = create_slide_data(response.content)
        
        # Step 4: Add basic metadata and calculate word counts
        if slide_data and "lesson_info" in slide_data:
            lesson_info = slide_data["lesson_info"]
            lesson_info["primary_source"] = "file_upload" if uploaded_files_content else "generated_content"
            lesson_info["target_level"] = "Cấp 3 (lớp 10-12)"
            
            # Calculate word counts and duration from tts_script
            slides = slide_data.get('slides', [])
            total_words = 0
            
            for slide in slides:
                tts_script = slide.get('tts_script', '')
                word_count = len(tts_script.split()) if tts_script else 0
                total_words += word_count
            
            # Calculate estimated duration (180 words per minute)
            estimated_duration_minutes = total_words / 180
            
            # Update lesson_info with calculated values
            lesson_info['total_words'] = total_words
            lesson_info['estimated_duration_minutes'] = round(estimated_duration_minutes, 1)
        
        logger.info(f"Successfully created slides with {slide_data.get('lesson_info', {}).get('slide_count', 0)} slides, {slide_data.get('lesson_info', {}).get('total_words', 0)} words, duration: {slide_data.get('lesson_info', {}).get('estimated_duration_minutes', 0):.1f} minutes")
        
        return {
            "success": True,
            "slide_data": slide_data,
        }
        
    except Exception as e:
        logger.error(f"Error creating slides: {e}")
        return {"success": False, "error": str(e), "slide_data": None}
