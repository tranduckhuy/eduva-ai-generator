from src.utils.logger import logger
from .tools import retrieve_document
from .func import create_slide_data, enhance_tts_script, generate_image_keywords
from .prompt import create_messages_for_llm


async def run_slide_creator(topic: str, uploaded_files_content: str = None, model_name: str = "gemini-2.0-flash"):
    """Optimized slide creator using centralized prompts, with enhanced TTS and image keywords"""
    try:
        logger.info(f"Creating slides for topic: {topic}")
        
        # Step 1: Always retrieve documents from vector store
        logger.info("Step 1: Retrieving documents from vector store...")
        
        rag_result = retrieve_document.invoke(topic)
        rag_context = rag_result.get("context_str", "")
        selected_documents = rag_result.get("selected_documents", [])
        
        logger.info(f"Retrieved {len(selected_documents)} documents from vector store")
        
        # Step 2: Build messages using centralized prompts
        logger.info("Step 2: Building context using centralized prompts...")
        
        prompt_messages = create_messages_for_llm(
            topic=topic,
            uploaded_files_content=uploaded_files_content,
            rag_context=rag_context
        )
        
        # Step 3: Call LLM to generate slides
        from src.config.llm import get_llm
        llm = get_llm(model_name)
        logger.info(f"Step 3: Generating slides with {model_name}...")
        
        response = await llm.ainvoke(prompt_messages)
        
        # Step 4: Parse and enhance response
        slide_data = create_slide_data(response.content)
        
        # Step 5: Post-process to ensure quality TTS and image keywords
        if slide_data and "slides" in slide_data:
            for slide in slide_data["slides"]:
                # Ensure TTS script is comprehensive
                tts_word_count = len(slide.get("tts_script", "").split())
                if tts_word_count < 100:
                    logger.info(f"Enhancing TTS script for slide {slide.get('slide_id', 'unknown')}")
                    slide["tts_script"] = enhance_tts_script(slide)
                
                # Ensure image keywords are specific and searchable
                current_keywords = slide.get("image_keywords", [])
                if len(current_keywords) < 4 or any(len(kw.split()) > 4 for kw in current_keywords):
                    logger.info(f"Improving image keywords for slide {slide.get('slide_id', 'unknown')}")
                    slide["image_keywords"] = generate_image_keywords(slide)
                
                # Calculate duration based on TTS script length
                word_count = len(slide.get("tts_script", "").split())
                slide["estimated_duration_seconds"] = max(60, min(240, int(word_count * 0.4)))
        
        # Step 7: Add metadata and source information
        if slide_data and "lesson_info" in slide_data:
            lesson_info = slide_data["lesson_info"]
            
            # Determine primary content source
            if uploaded_files_content and uploaded_files_content.strip():
                lesson_info["primary_source"] = "file_upload"
                lesson_info["has_uploaded_content"] = True
                lesson_info["content_sources"] = ["file_upload", "vector_store"] if rag_context else ["file_upload"]
            else:
                lesson_info["primary_source"] = "vector_store"
                lesson_info["has_uploaded_content"] = False
                lesson_info["content_sources"] = ["vector_store"]
                
            lesson_info["rag_documents_count"] = len(selected_documents)
            lesson_info["target_level"] = "Cấp 3 (lớp 10-12)"
            
            # Calculate total estimated duration
            if "slides" in slide_data:
                total_seconds = sum(slide.get("estimated_duration_seconds", 90) for slide in slide_data["slides"])
                lesson_info["estimated_duration_minutes"] = max(1, total_seconds // 60)
        
        # Create enhanced RAG sources for tracking
        rag_sources = []
        for i, doc in enumerate(selected_documents):
            if hasattr(doc, 'page_content'):
                rag_sources.append({
                    "source_id": f"rag_{i+1}",
                    "source_type": "vector_store",
                    "title": getattr(doc, 'metadata', {}).get("title", f"Tài liệu {i+1}"),
                    "content_preview": (doc.page_content[:150] + "...") if len(doc.page_content) > 150 else doc.page_content,
                    "metadata": getattr(doc, 'metadata', {})
                })
        
        slide_count = slide_data.get('lesson_info', {}).get('slide_count', 0)
        duration = slide_data.get('lesson_info', {}).get('estimated_duration_minutes', 0)
        
        logger.info(f"Successfully created {slide_count} slides with {duration} minutes total duration")
        logger.info(f"Enhanced TTS scripts and optimized image keywords for better searchability")
        
        return {
            "success": True,
            "slide_data": slide_data,
            "selected_documents": selected_documents,
            "rag_sources": rag_sources,
        }
        
    except Exception as e:
        logger.error(f"Error creating slides: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e), "slide_data": None}
