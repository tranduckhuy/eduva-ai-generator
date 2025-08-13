import os
from src.utils.logger import logger
from .prompt import create_prompt_template
from src.config.llm import get_llm
from src.agents.lesson_creator.schemas import SlideDeck

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL")

WORDS_PER_MINUTE = 200

async def run_slide_creator(
    topic: str, 
    uploaded_files_content: str = None,
    model_name: str = DEFAULT_MODEL
) -> dict:
    """Simplified slide creator focused on topic and file upload only"""
    try:
        logger.info(f"Creating slides for topic: {topic}")
        
        prompt = create_prompt_template()
        llm = get_llm(model_name)
        logger.info(f"Generating slides with {model_name}...")
        structured_llm = llm.with_structured_output(SlideDeck)

        chain = prompt | structured_llm

        slide_deck = await chain.ainvoke({
            "topic": topic,
            "uploaded_files_content": uploaded_files_content or ""
        })

        if not slide_deck:
            raise ValueError("Model returned None, possibly due to content filtering.")    
        
        total_words = sum(len(slide.tts_script.split()) for slide in slide_deck.slides)
        estimated_duration = round((total_words / WORDS_PER_MINUTE), 1)
        
        slide_deck.lesson_info.total_words = total_words
        slide_deck.lesson_info.estimated_duration_minutes = estimated_duration
        
        logger.info(f"Successfully created slides. Title: '{slide_deck.lesson_info.title}', Slides: {len(slide_deck.slides)}, Words: {total_words}")
        
        return {
            "success": True,
            "slide_data": slide_deck.model_dump(),
        }
        
    except Exception as e:
        logger.error(f"Error creating slides: {e}", exc_info=True)
        return {"success": False, "error": str(e), "slide_data": None}
