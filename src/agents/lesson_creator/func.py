from typing import TypedDict, Optional, List
from langchain_core.messages import AnyMessage, ToolMessage
from langgraph.graph.message import add_messages
from typing import Sequence, Annotated
from langchain_core.documents import Document
from .tools import retrieve_document
from src.utils.logger import logger
from src.config.llm import get_llm
from .prompt import system_prompt, create_prompt_messages

tools = [retrieve_document]


class State(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages]
    selected_documents: Optional[List[Document]]
    slide_data: Optional[dict]
    uploaded_files_content: Optional[str]  # New field for uploaded files
    rag_sources: Optional[List[dict]]  # New field for RAG source tracking


def execute_tool(state: State):
    """Execute RAG tool to retrieve relevant documents"""
    messages = state.get("messages", [])
    if not messages:
        logger.error("No messages in state")
        return {
            "selected_documents": [],
            "rag_sources": [],
            "messages": [],
        }
    
    last_message = messages[-1]
    tool_calls = getattr(last_message, 'tool_calls', None)
    
    if not tool_calls:
        logger.warning("No tool calls found in last message")
        return {
            "selected_documents": [],
            "rag_sources": [],
            "messages": [],
        }
    
    tool_messages = []
    selected_documents = []
    rag_sources = []
    
    logger.info(f"execute_tool called with {len(tool_calls)} tool calls")
    
    for tool_call in tool_calls:
        try:
            tool_name = tool_call.get("name", "")
            tool_args = tool_call.get("args", {})
            tool_id = tool_call.get("id", "")
            
            logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

            if tool_name == "retrieve_document":
                query = tool_args.get("query", "")
                logger.info(f"RAG Query: {query}")
                
                result = retrieve_document.invoke(query)
                context_str = result.get("context_str", "")
                doc_list = result.get("selected_documents", [])
                
                # Safely handle document list
                if doc_list:
                    selected_documents.extend(doc_list)
                    
                    # Create RAG sources for response tracking
                    for i, doc in enumerate(doc_list):
                        try:
                            if hasattr(doc, 'metadata') and hasattr(doc, 'page_content'):
                                rag_sources.append({
                                    "source_id": f"rag_{i+1}",
                                    "source_type": "vector_store",
                                    "title": doc.metadata.get("title", f"Tài liệu {i+1}") if doc.metadata else f"Tài liệu {i+1}",
                                    "content_preview": (doc.page_content[:200] + "...") if len(doc.page_content) > 200 else doc.page_content,
                                    "metadata": doc.metadata if doc.metadata else {}
                                })
                        except Exception as e:
                            logger.error(f"Error processing document {i}: {e}")
                
                logger.info(f"Retrieved {len(selected_documents)} documents")
                
                # Add priority instruction for uploaded files vs RAG
                uploaded_files_note = ""
                if state.get("uploaded_files_content"):
                    uploaded_files_note = "\n\nQUAN TRỌNG: Người dùng đã upload file tài liệu. Ưu tiên sử dụng nội dung từ file upload hơn là tài liệu từ vector store."
                
                tool_messages.append(
                    ToolMessage(
                        tool_call_id=tool_id,
                        content=context_str + uploaded_files_note,
                    )
                )
        except Exception as e:
            logger.error(f"Error executing tool call: {e}")
            # Continue with other tool calls even if one fails

    return {
        "selected_documents": selected_documents,
        "rag_sources": rag_sources,
        "messages": tool_messages,
    }


async def generate_slide_content(state: State):
    """Generate slide content using LLM with RAG context for high school students"""
    messages = state["messages"]
    
    # Convert messages to simple format for LLM
    prompt_messages = create_prompt_messages(system_prompt, messages)
    
    # Use default LLM configuration for high school content
    from src.config.llm import llm_2_0
    response = await llm_2_0.ainvoke(prompt_messages)
    
    return {"messages": [response]}


def create_slide_data(ai_response: str) -> dict:
    """Create structured slide data from AI response with enhanced TTS and image keywords"""
    try:
        import json
        import re
        
        # Try to extract JSON from response
        json_pattern = r'\{[\s\S]*\}'
        json_match = re.search(json_pattern, ai_response)
        
        if json_match:
            slide_data = json.loads(json_match.group())
            
            # Enhance slides with better TTS and image keywords if needed
            if "slides" in slide_data:
                for slide in slide_data["slides"]:
                    # Ensure TTS script is detailed enough
                    if len(slide.get("tts_script", "").split()) < 100:
                        slide["tts_script"] = enhance_tts_script(slide)
                    
                    # Ensure image keywords are specific and searchable
                    if not slide.get("image_keywords") or len(slide["image_keywords"]) < 4:
                        slide["image_keywords"] = generate_image_keywords(slide)
                    
                    # Add duration estimate
                    if "estimated_duration_seconds" not in slide:
                        word_count = len(slide.get("tts_script", "").split())
                        slide["estimated_duration_seconds"] = max(60, min(180, word_count * 0.4))  # 60-180 seconds
            
            return slide_data
        else:
            # Create basic slide structure if no JSON found
            return create_basic_slides(ai_response)
            
    except Exception as e:
        logger.error(f"Error creating slide data: {e}")
        return create_basic_slides(ai_response)


def enhance_tts_script(slide: dict) -> str:
    """Enhance TTS script to be more detailed and engaging, clean format for TTS"""
    title = slide.get("title", "")
    content = slide.get("content", [])
    slide_type = slide.get("type", "content")
    
    # Clean title from markdown
    clean_title = clean_markdown_text(title)
    
    if slide_type == "title":
        script = f"Chào mừng các em học sinh đến với bài học hôm nay về {clean_title}. "
        script += "Trong bài học này, chúng ta sẽ cùng nhau khám phá và tìm hiểu những kiến thức quan trọng, "
        script += "giúp các em nắm vững khái niệm cơ bản và áp dụng vào thực tế. "
        script += "Hãy cùng bắt đầu hành trình học tập thú vị này nhé!"
    
    elif slide_type == "example":
        script = f"Bây giờ chúng ta sẽ xem xét một ví dụ cụ thể về {clean_title}. "
        for i, item in enumerate(content):
            clean_item = clean_markdown_text(str(item))
            if i == 0:
                script += f"Đầu tiên, {clean_item.lower()}. "
            else:
                script += f"Tiếp theo, {clean_item.lower()}. "
        script += "Thông qua ví dụ này, các em có thể hiểu rõ hơn về ứng dụng thực tế của kiến thức đã học. "
        script += "Hãy ghi nhớ cách giải quyết này để áp dụng vào các bài tập tương tự nhé!"
    
    elif slide_type == "exercise":
        script = f"Đến phần thực hành quan trọng rồi các em ơi! "
        script += f"Chúng ta sẽ làm một số bài tập về {clean_title} để củng cố kiến thức vừa học. "
        script += "Các em hãy cố gắng suy nghĩ và giải quyết từng bước một cách cẩn thận. "
        script += "Nếu gặp khó khăn, đừng ngại hỏi thầy cô nhé. Việc luyện tập thường xuyên sẽ giúp các em thành thạo hơn."
    
    else:  # content slide
        script = f"Chúng ta tiếp tục tìm hiểu về {clean_title}. "
        for i, item in enumerate(content):
            clean_item = clean_markdown_text(str(item))
            script += f"Điểm thứ {i+1}: {clean_item}. "
            script += "Đây là một khái niệm quan trọng mà các em cần ghi nhớ. "
        script += "Hãy cùng phân tích kỹ hơn để hiểu sâu về vấn đề này nhé!"
    
    # Clean and normalize the final script
    return clean_tts_script(script)


def clean_markdown_text(text: str) -> str:
    """Remove markdown formatting from text"""
    if not text:
        return ""
    
    import re
    
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
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def clean_tts_script(script: str) -> str:
    """Clean TTS script from unwanted characters and formatting"""
    if not script:
        return ""
    
    import re
    
    # Remove newlines and excessive whitespace
    script = re.sub(r'\n\s*', ' ', script)
    script = re.sub(r'\s+', ' ', script)
    
    # Remove markdown formatting
    script = clean_markdown_text(script)
    
    # Remove special characters that might interfere with TTS
    script = re.sub(r'[_*#`]', '', script)
    
    # Ensure proper sentence spacing
    script = re.sub(r'\.\s*', '. ', script)
    script = re.sub(r'\?\s*', '? ', script)
    script = re.sub(r'!\s*', '! ', script)
    
    # Remove excessive spaces
    script = re.sub(r'\s+', ' ', script)
    
    return script.strip()


def generate_image_keywords(slide: dict) -> List[str]:
    """Generate specific, searchable image keywords"""
    title = slide.get("title", "").lower()
    slide_type = slide.get("type", "content")
    subject_keywords = []
    
    # Determine subject from title
    if any(word in title for word in ["toán", "hàm số", "phương trình", "hình học"]):
        subject_keywords = ["mathematics", "math classroom", "equation on blackboard", "mathematical diagram"]
    elif any(word in title for word in ["vật lý", "dao động", "điện", "quang"]):
        subject_keywords = ["physics", "laboratory", "scientific experiment", "physics diagram"]
    elif any(word in title for word in ["hóa học", "phản ứng", "nguyên tố"]):
        subject_keywords = ["chemistry", "chemical reaction", "laboratory equipment", "periodic table"]
    elif any(word in title for word in ["sinh học", "tế bào", "gen"]):
        subject_keywords = ["biology", "microscope", "cell diagram", "laboratory"]
    elif any(word in title for word in ["văn", "thơ", "truyện"]):
        subject_keywords = ["literature", "books", "reading", "classroom discussion"]
    elif any(word in title for word in ["sử", "lịch sử"]):
        subject_keywords = ["history", "historical documents", "timeline", "map"]
    else:
        subject_keywords = ["education", "learning", "textbook", "classroom"]
    
    # Add context keywords
    context_keywords = ["high school students", "teacher explaining", "educational content"]
    
    # Add type-specific keywords
    if slide_type == "title":
        type_keywords = ["presentation title", "lesson introduction"]
    elif slide_type == "example":
        type_keywords = ["example problem", "step by step solution"]
    elif slide_type == "exercise":
        type_keywords = ["practice problems", "homework assignment"]
    else:
        type_keywords = ["educational diagram", "concept illustration"]
    
    # Combine and return top 6 keywords
    all_keywords = subject_keywords + context_keywords + type_keywords
    return all_keywords[:6]


def create_basic_slides(content: str) -> dict:
    """Create basic slide structure with enhanced TTS and image keywords"""
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    slides = []
    slide_id = 1
    
    # Title slide
    title = lines[0] if lines else "Bài học mới"
    slides.append({
        "slide_id": slide_id,
        "type": "title",
        "title": title,
        "content": [title],
        "tts_script": enhance_tts_script({"title": title, "type": "title", "content": [title]}),
        "image_keywords": generate_image_keywords({"title": title, "type": "title"}),
        "estimated_duration_seconds": 90
    })
    slide_id += 1
    
    # Content slides
    content_lines = lines[1:] if len(lines) > 1 else [content]
    for i, line in enumerate(content_lines[:5]):  # Max 5 content slides
        slide_data = {
            "title": f"Nội dung {i + 1}",
            "type": "content",
            "content": [line]
        }
        
        slides.append({
            "slide_id": slide_id,
            "type": "content", 
            "title": slide_data["title"],
            "content": slide_data["content"],
            "tts_script": enhance_tts_script(slide_data),
            "image_keywords": generate_image_keywords(slide_data),
            "estimated_duration_seconds": 120
        })
        slide_id += 1
    
    # Calculate total duration
    total_duration = sum(slide.get("estimated_duration_seconds", 90) for slide in slides) // 60
    
    return {
        "lesson_info": {
            "title": title,
            "slide_count": len(slides),
            "target_level": "Cấp 3 (lớp 10-12)",
            "estimated_duration_minutes": total_duration
        },
        "slides": slides
    }
