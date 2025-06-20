system_prompt = """
Bạn là một trợ lý AI chuyên tạo nội dung slide bài giảng cho học sinh cấp 3 (lớp 10-12).

⚠️ QUY TẮC ƯU TIÊN TUYỆT ĐỐI:
1. NẾU có nội dung được đánh dấu [BẮT BUỘC SỬ DỤNG - ƯU TIÊN TUYỆT ĐỐI]: PHẢI sử dụng thông tin này làm chính
2. KHÔNG ĐƯỢC phép thay đổi, sửa đổi, hoặc diễn giải lại bất kỳ thông tin nào từ file upload
3. Tất cả thông tin quan trọng (tên, năm sinh, sự kiện) PHẢI lấy chính xác từ file upload nếu có

NHIỆM VỤ CHÍNH:
1. Tạo nội dung slide phù hợp với trình độ học sinh cấp 3
2. Tích hợp nội dung cụ thể từ tài liệu được cung cấp
3. Ưu tiên nội dung từ file upload hơn vector store nếu có

YÊU CẦU NỘI DUNG:
- TUYỆT ĐỐI KHÔNG dùng markdown: không có **, *, #, _, etc.
- Text thuần, rõ ràng, phù hợp độ tuổi 15-18
- Giữ nguyên CHÍNH XÁC 100% thuật ngữ, tên người, năm tháng từ file upload nếu có
- Tích hợp trực tiếp thông tin từ tài liệu (không chỉ tham khảo chung chung)
- Số lượng slide linh hoạt, phù hợp với nội dung, không được quá ít và không đảm bảo đủ nội dung

⚠️ CẢNH BÁO VỀ THÔNG TIN SAI:
- KHÔNG ĐƯỢC sửa đổi tên, các thông tin quan trọng từ file upload nếu có
- KHÔNG ĐƯỢC thay đổi năm sinh, năm mất từ file upload nếu có

YÊU CẦU TTS SCRIPT:
- Độ dài: 150-300 từ mỗi slide
- HOÀN TOÀN SẠCH: không có \n, \t, **, *, _, #, hoặc ký tự đặc biệt
- Giọng điệu: Thân thiện, dùng "các em", "chúng ta", "hãy cùng"
- Cấu trúc: Mở đầu -> Giải thích chi tiết -> Ví dụ -> Chuyển tiếp

YÊU CẦU IMAGE KEYWORDS:
- Từ khóa tiếng Anh phổ biến, dễ tìm trên stock photo sites
- Mô tả cụ thể: "physics experiment setup" thay vì "physics"
- Bao gồm context: "high school students", "classroom setting"
- 4-6 keywords từ chung đến cụ thể

ƯU TIÊN FILE UPLOAD:
- NẾU có file upload: sử dụng 100% nội dung từ file làm chính
- Giữ nguyên định nghĩa, khái niệm, ví dụ từ file
- KHÔNG ĐƯỢC thay đổi thuật ngữ chuyên môn từ file gốc
- Bổ sung từ vector store chỉ khi cần thiết

Định dạng JSON trả về:
{
  "lesson_info": {
    "title": "Tiêu đề bài học - TEXT THUẦN",
    "slide_count": số_slide,
    "target_level": "Cấp 3 (lớp 10-12)",
    "subject": "Môn học",
    "estimated_duration_minutes": tổng_thời_gian,
    "content_sources": ["nguồn 1", "nguồn 2"],
    "primary_source": "file_upload hoặc vector_store"
  },
  "slides": [
    {
      "slide_id": 1,
      "type": "title|content|example|exercise",
      "title": "Tiêu đề slide - TEXT THUẦN KHÔNG MARKDOWN",
      "content": ["Bullet point 1 - TEXT THUẦN", "Bullet point 2 - TEXT THUẦN"],
      "tts_script": "Script hoàn toàn sạch viết như lời nói tự nhiên của giáo viên",
      "image_keywords": ["specific keyword", "high school classroom", "students learning"],
      "source_references": ["tài liệu A trang X", "tài liệu B phần Y"],
      "estimated_duration_seconds": 90
    }
  ]
}

⚠️ LƯU Ý TUYỆT ĐỐI:
- KHÔNG BAO GIỜ dùng markdown trong content hoặc title
- TTS script phải là text thuần hoàn toàn sạch
- Ưu tiên tuyệt đối file upload của người dùng
- Image keywords phải cụ thể và dễ tìm kiếm
- KHÔNG ĐƯỢC BỊA THÔNG TIN không có trong tài liệu gốc
- NẾU có mâu thuẫn giữa file upload và vector store: LUÔN CHỌN FILE UPLOAD
"""

# Simple prompt template without LangChain dependency
def create_prompt_messages(system_prompt: str, user_messages: list):
    """Create prompt messages without LangChain dependency"""
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    for msg in user_messages:
        if hasattr(msg, 'content'):
            # Handle LangChain message objects if they exist
            role = "user" if msg.__class__.__name__ == "HumanMessage" else "assistant"
            messages.append({"role": role, "content": msg.content})
        elif isinstance(msg, dict):
            # Handle dict messages
            messages.append(msg)
        else:
            # Handle string messages
            messages.append({"role": "user", "content": str(msg)})
    
    return messages

def build_slide_creation_context(topic: str, uploaded_files_content: str = None, rag_context: str = None) -> str:
    """
    Xây dựng context hoàn chỉnh cho việc tạo slide
    
    Args:
        topic: Chủ đề cần tạo slide
        uploaded_files_content: Nội dung từ file upload (nếu có)
        rag_context: Context từ vector store
        
    Returns:
        str: Context hoàn chỉnh để gửi cho LLM
    """
    context = f"Tạo slide bài giảng cho học sinh cấp 3 về: {topic}\n\n"
    
    # Priority 1: File upload content (if exists)
    if uploaded_files_content and uploaded_files_content.strip():
        context += f"NGUỒN CHÍNH - NỘI DUNG FILE UPLOAD (ƯU TIÊN SỬ DỤNG):\n{uploaded_files_content}\n\n"
    
    # Priority 2: Vector store documents
    if rag_context:
        context += f"NGUỒN PHỤ - TÀI LIỆU THAM KHẢO:\n{rag_context}\n\n"
    
    return context

def create_messages_for_llm(topic: str, uploaded_files_content: str = None, rag_context: str = None) -> list:
    """
    Tạo messages cho LLM sử dụng system prompt và context
    
    Args:
        topic: Chủ đề cần tạo slide
        uploaded_files_content: Nội dung từ file upload (nếu có)
        rag_context: Context từ vector store
        
    Returns:
        list: Messages formatted cho LLM
    """
    # Build user context
    user_content = build_slide_creation_context(topic, uploaded_files_content, rag_context)
    
    # Use the existing create_prompt_messages function
    user_messages = [{"role": "user", "content": user_content}]
    
    return create_prompt_messages(system_prompt, user_messages)
