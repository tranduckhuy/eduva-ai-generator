from src.utils.logger import logger
from .tools import retrieve_document
from .func import create_slide_data, enhance_tts_script, generate_image_keywords
from .cleaning import clean_all_slide_content


async def run_slide_creator(topic: str, uploaded_files_content: str = None, model_name: str = "gemini-2.0-flash"):
    """Optimized slide creator without LangChain dependencies, with enhanced TTS and image keywords"""
    try:
        logger.info(f"Creating slides for topic: {topic}")
        
        # Step 1: Always retrieve documents from vector store
        logger.info("Step 1: Retrieving documents from vector store...")
        
        rag_result = retrieve_document.invoke(topic)
        rag_context = rag_result.get("context_str", "")
        selected_documents = rag_result.get("selected_documents", [])
        
        logger.info(f"Retrieved {len(selected_documents)} documents from vector store")
        
        # Step 2: Build comprehensive context with file upload priority
        full_context = f"Tạo slide bài giảng cho học sinh cấp 3 về: {topic}\n\n"
        
        # Priority 1: File upload content (if exists)
        if uploaded_files_content and uploaded_files_content.strip():
            full_context += f"NGUỒN CHÍNH - NỘI DUNG FILE UPLOAD (ƯU TIÊN SỬ DỤNG):\n{uploaded_files_content}\n\n"
            logger.info(f"Using uploaded file content: {len(uploaded_files_content)} chars")
        
        # Priority 2: Vector store documents
        if rag_context:
            full_context += f"NGUỒN PHỤ - TÀI LIỆU THAM KHẢO:\n{rag_context}\n\n"
        
        # Step 3: Enhanced instructions for better TTS and image keywords
        full_context += """
YÊU CẦU TẠO SLIDE CHO HỌC SINH CẤP 3:

1. NỘI DUNG - QUAN TRỌNG:
   - NẾU CÓ FILE UPLOAD: Sử dụng 100% nội dung từ file làm chính, giữ nguyên mọi định nghĩa, khái niệm, ví dụ
   - TUYỆT ĐỐI KHÔNG sửa đổi thuật ngữ khoa học từ file gốc
   - Bổ sung từ vector store chỉ khi cần thiết
   - KHÔNG BAO GIỜ dùng markdown: không có **, *, #, _, etc.
   - Text thuần, rõ ràng, phù hợp độ tuổi 15-18

2. TTS SCRIPT - CỰC KỲ QUAN TRỌNG:
   - Độ dài: 150-300 từ mỗi slide (đủ dài để tạo audio hoàn chỉnh)
   - HOÀN TOÀN SẠCH: không có \n, \t, **, *, _, #, hoặc bất kỳ ký tự đặc biệt nào
   - Chỉ dùng text thuần như lời nói tự nhiên của giáo viên
   - Giọng điệu: Thân thiện, nhiệt tình, dùng "các em", "chúng ta", "hãy cùng"
   - Cấu trúc: Chào mừng -> Giải thích chi tiết -> Ví dụ từ tài liệu -> Chuyển tiếp

3. IMAGE KEYWORDS - CỤ THỂ VÀ DỄ TÌM:
   - Từ khóa tiếng Anh phổ biến trên stock photo sites
   - Mô tả rõ ràng: "physics experiment setup" thay vì "physics"
   - Context: "high school students", "classroom setting", "textbook illustration"
   - 4-6 keywords từ chung đến cụ thể

4. TÍCH HỢP FILE UPLOAD:
   - Ưu tiên tuyệt đối nội dung từ file user upload
   - Giữ nguyên cấu trúc bài học từ file
   - Trích xuất trực tiếp định nghĩa, công thức, ví dụ từ file
   - Không thay đổi hoặc diễn giải lại nội dung file gốc

TRẢ VỀ JSON HOÀN TOÀN SẠCH:
{
  "lesson_info": {
    "title": "Tiêu đề từ file upload hoặc topic - TEXT THUẦN",
    "slide_count": số_slide_phù_hợp,
    "target_level": "Cấp 3 (lớp 10-12)",
    "subject": "Môn học từ file hoặc suy luận",
    "estimated_duration_minutes": tổng_thời_gian,
    "content_sources": ["file_upload ưu tiên", "vector_store phụ"],
    "primary_source": "file_upload hoặc vector_store"
  },
  "slides": [
    {
      "slide_id": 1,
      "type": "title|content|example|exercise",
      "title": "Tiêu đề slide từ file - HOÀN TOÀN KHÔNG MARKDOWN",
      "content": ["Bullet point 1 từ file - TEXT THUẦN", "Bullet point 2 từ file - TEXT THUẦN"],
      "tts_script": "Script hoàn toàn sạch không có ký tự đặc biệt viết như giáo viên đang nói chuyện với học sinh một cách tự nhiên và thân thiện",
      "image_keywords": ["specific visual concept", "high school classroom", "students engaged", "educational material"],
      "source_references": ["File upload trang/phần X", "Vector store doc Y"],
      "estimated_duration_seconds": 90
    }
  ]
}

LƯU Ý TUYỆT ĐỐI:
- Nếu có công thức trong file: giữ nguyên hoàn toàn
- Nếu có thuật ngữ chuyên môn: không thay đổi
- TTS script: viết như đang nói, không có formatting
- Content: text thuần, không bold, italic, header gì cả
"""
        
        # Step 4: Call LLM to generate slides
        from src.config.llm import get_llm
        llm = get_llm(model_name)
        logger.info(f"Step 2: Generating slides with {model_name}...")
        
        response = await llm.ainvoke([{"role": "user", "content": full_context}])
        
        # Step 5: Parse and enhance response
        slide_data = create_slide_data(response.content)
        
        # Step 5.5: Clean all markdown and special characters from slide data
        slide_data = clean_all_slide_content(slide_data)
        
        # Step 6: Post-process to ensure quality TTS and image keywords
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
