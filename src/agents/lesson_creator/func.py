from typing import TypedDict, Optional, List
from langchain_core.messages import AnyMessage, ToolMessage
from langgraph.graph.message import add_messages
from typing import Sequence, Annotated
from langchain_core.messages import RemoveMessage
from langchain_core.documents import Document
from .tools import retrieve_document, create_structured_lesson_content, duckduckgo_search
from src.utils.logger import logger
from src.config.llm import get_llm
from .prompt import system_prompt, template_prompt
import json

tools = [retrieve_document, create_structured_lesson_content, duckduckgo_search]


class State(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages]
    selected_ids: Optional[List[str]]
    selected_documents: Optional[List[Document]]
    slide_data: Optional[dict]  # Thêm để lưu structured slide data


def trim_history(state: State):
    history = state.get("messages", [])
    tool_names = state.get("tools", [])

    if len(history) > 10:
        num_to_remove = len(history) - 10
        remove_messages = [
            RemoveMessage(id=history[i].id) for i in range(num_to_remove)
        ]
        return {
            "messages": remove_messages,
            "selected_ids": [],
            "selected_documents": [],
        }

    return {}


def execute_tool(state: State):
    tool_calls = state["messages"][-1].tool_calls
    tool_names = state.get("tools", [])
    tool_name_to_func = {tool.name: tool for tool in tools}
    tool_functions = [
        tool_name_to_func[name] for name in tool_names if name in tool_name_to_func
    ]

    selected_ids = []
    selected_documents = []
    tool_messages = []
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]

        tool_func = tool_name_to_func.get(tool_name)
        if tool_func:
            if tool_name == "retrieve_document":
                documents = tool_func.invoke(tool_args.get("query"))
                documents = dict(documents)
                context_str = documents.get("context_str", "")
                selected_documents = documents.get("selected_documents", [])
                selected_ids = documents.get("selected_ids", [])
                if documents:
                    tool_messages.append(
                        ToolMessage(
                            tool_call_id=tool_id,
                            content=context_str,
                        )
                    )
                continue
            tool_response = tool_func.invoke(tool_args)
            print(f"tool_response: {tool_response}")
            tool_messages.append(
                ToolMessage(
                    tool_call_id=tool_id,
                    content=tool_response,
                )
            )

    return {
        "selected_ids": selected_ids,
        "selected_documents": selected_documents,
        "messages": tool_messages,
    }


async def generate_answer_rag(state: State):
    global system_prompt
    messages = state["messages"]
    # Sử dụng tất cả tools có sẵn để đảm bảo RAG hoạt động đầy đủ
    tool_names = [tool.name for tool in tools]
    model_name = state.get("model_name", "gemini-2.0-flash")
    api_key = state.get("api_key", None)
    
    # Bind tất cả tools để AI có thể truy xuất thông tin đầy đủ
    llm_call = template_prompt | get_llm(model_name, api_key).bind_tools(tools)

    response = await llm_call.ainvoke(
        {
            "system_prompt": system_prompt,
            "messages": messages,
        }
    )

    return {"messages": response}


def extract_slide_data(content: str) -> dict:
    """
    Extract structured slide data from AI response - now expects complete JSON structure
    """
    try:
        # Try to find JSON in the response
        import re
        json_pattern = r'\{[\s\S]*\}'
        json_match = re.search(json_pattern, content)
        
        if json_match:
            json_str = json_match.group()
            slide_data = json.loads(json_str)
            
            # Validate required fields
            if "lesson_info" in slide_data and "slides" in slide_data:
                return slide_data
            else:
                logger.warning("JSON missing required fields, creating fallback")
                return create_fallback_slide_data(content)
        else:
            # Try to extract from tool response if JSON wasn't found in text
            return parse_tool_response_to_slide_data(content)
            
    except Exception as e:
        logger.error(f"Error extracting slide data: {e}")
        return create_fallback_slide_data(content)


def parse_tool_response_to_slide_data(content: str) -> dict:
    """
    Parse content that might contain structured lesson data from tools
    """
    try:
        # Look for structured lesson content in the response
        if "lesson_info" in content or "slides" in content:
            # Try to extract the JSON structure
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                return json.loads(json_str)
        
        return create_enhanced_slide_data(content)
        
    except Exception as e:
        logger.error(f"Error parsing tool response: {e}")
        return create_fallback_slide_data(content)


def create_enhanced_slide_data(content: str) -> dict:
    """
    Create enhanced slide data with better structure for video pipeline
    """
    # Extract key information from content
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    # Try to identify topic, subject, grade from content
    topic = "Bài giảng"
    subject = "Chưa xác định"
    grade = "Cấp 3"
    
    # Look for subject indicators
    subjects = {
        "toán": "Toán", "hóa": "Hóa học", "lý": "Vật lý", 
        "văn": "Ngữ văn", "sử": "Lịch sử", "địa": "Địa lý",
        "sinh": "Sinh học", "anh": "Tiếng Anh"
    }
    
    content_lower = content.lower()
    for key, value in subjects.items():
        if key in content_lower:
            subject = value
            break
    
    # Look for grade indicators
    for i in range(10, 13):
        if f"lớp {i}" in content_lower or f"lớp{i}" in content_lower:
            grade = f"lớp {i}"
            break
    
    # Create structured slides
    slides = []
    
    # Title slide
    slides.append({
        "slide_id": 1,
        "type": "title",
        "title": topic,
        "subtitle": f"{subject} - {grade}",
        "content": f"Chào mừng các em đến với bài học về {topic}",
        "duration_seconds": 30,
        "tts_script": {
            "text": f"Xin chào các em học sinh {grade}! Hôm nay cô sẽ cùng các em tìm hiểu về {topic} trong môn {subject}. Các em hãy chuẩn bị tinh thần để cùng cô khám phá những kiến thức thú vị nhé!",
            "speed": "normal",
            "pause_duration": 2.0
        },
        "visual_elements": {
            "background_color": "#f8f9fa",
            "text_color": "#212529",
            "font_size": "large",
            "layout": "center",
            "image_suggestions": [
                {
                    "type": "subject_icon",
                    "description": f"Biểu tượng môn {subject}",
                    "keywords": [subject.lower(), "education", "school", "icon"],
                    "position": "top-right",
                    "size": "medium"
                }
            ]
        }
    })
    
    # Content slides - split content into logical sections
    content_sections = split_content_into_sections(content, max_sections=6)
    slide_id = 2
    
    for section in content_sections:
        slides.append({
            "slide_id": slide_id,
            "type": "content",
            "title": f"Nội dung {slide_id - 1}",
            "content": section["content"],
            "duration_seconds": max(60, len(section["content"]) // 10),
            "tts_script": {
                "text": section["tts_text"],
                "speed": "normal",
                "pause_duration": 1.5
            },
            "visual_elements": {
                "background_color": "#ffffff",
                "text_color": "#333333",
                "font_size": "medium",
                "layout": "bullet-points",
                "image_suggestions": [
                    {
                        "type": "content_illustration",
                        "description": f"Hình ảnh minh họa cho {section['title']}",
                        "keywords": [topic.lower(), subject.lower(), "illustration"],
                        "position": "right",
                        "size": "medium"
                    }
                ]
            }
        })
        slide_id += 1
    
    # Summary slide
    slides.append({
        "slide_id": slide_id,
        "type": "summary",
        "title": "Tóm tắt bài học",
        "content": f"Tóm tắt những điểm chính về {topic}",
        "duration_seconds": 60,
        "tts_script": {
            "text": f"Vậy là chúng ta đã cùng nhau tìm hiểu về {topic}. Các em hãy ghi nhớ những điểm chính đã học. Về nhà các em hãy ôn tập và làm bài tập để củng cố kiến thức nhé!",
            "speed": "normal",
            "pause_duration": 1.0
        },
        "visual_elements": {
            "background_color": "#e9ecef",
            "text_color": "#212529",
            "font_size": "medium",
            "layout": "summary-list",
            "image_suggestions": [
                {
                    "type": "summary_graphic",
                    "description": "Biểu đồ tóm tắt bài học",
                    "keywords": ["summary", "conclusion", subject.lower()],
                    "position": "left",
                    "size": "medium"
                }
            ]
        }
    })
    
    return {
        "lesson_info": {
            "title": topic,
            "subject": subject,
            "grade": grade,
            "duration_minutes": sum(slide["duration_seconds"] for slide in slides) // 60,
            "estimated_slides": len(slides),
            "difficulty_level": "intermediate",
            "learning_objectives": [
                f"Hiểu được khái niệm cơ bản về {topic}",
                f"Áp dụng kiến thức {topic} vào thực tế",
                f"Liên kết {topic} với các kiến thức đã học"
            ]
        },
        "slides": slides,
        "metadata": {
            "created_timestamp": "2025-06-08",
            "total_duration_seconds": sum(slide["duration_seconds"] for slide in slides),
            "slide_count": len(slides),
            "content_source": "AI-generated with educational content",
            "tts_voice_settings": {
                "voice_type": "vietnamese_female_teacher",
                "speech_rate": 1.0,
                "pitch": 0.0,
                "volume": 0.8
            },
            "reveal_js_config": {
                "theme": "white",
                "transition": "slide",
                "controls": True,
                "progress": True,
                "center": True
            }
        }
    }


def split_content_into_sections(content: str, max_sections: int = 6) -> list:
    """
    Split content into logical sections for slides
    """
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    sections = []
    
    current_section = {"title": "", "content": "", "tts_text": ""}
    lines_per_section = max(len(lines) // max_sections, 3)
    
    for i, line in enumerate(lines):
        if len(current_section["content"]) < 300:  # Limit content per slide
            current_section["content"] += line + "\n"
            current_section["tts_text"] += line + ". "
        
        if (i + 1) % lines_per_section == 0 or i == len(lines) - 1:
            if current_section["content"]:
                current_section["title"] = current_section["content"].split('\n')[0][:50] + "..."
                sections.append(current_section)
                current_section = {"title": "", "content": "", "tts_text": ""}
    
    return sections[:max_sections]


def create_fallback_slide_data(content: str) -> dict:
    """
    Create basic slide data when all parsing fails
    """
    return {
        "lesson_info": {
            "title": "Bài giảng",
            "subject": "Chưa xác định",
            "grade": "Cấp 3",
            "duration_minutes": 10,
            "estimated_slides": 2,
            "difficulty_level": "basic",
            "learning_objectives": ["Hiểu nội dung bài học"]
        },
        "slides": [
            {
                "slide_id": 1,
                "type": "title",
                "title": "Bài giảng",
                "content": "Nội dung bài giảng",
                "duration_seconds": 30,
                "tts_script": {
                    "text": "Xin chào các em! Hôm nay chúng ta sẽ cùng nhau học bài mới.",
                    "speed": "normal",
                    "pause_duration": 2.0
                },
                "visual_elements": {
                    "background_color": "#f8f9fa",
                    "text_color": "#212529",
                    "font_size": "large",
                    "layout": "center",
                    "image_suggestions": []
                }
            },
            {
                "slide_id": 2,
                "type": "content",
                "title": "Nội dung chính",
                "content": content[:300] + "..." if len(content) > 300 else content,
                "duration_seconds": 120,
                "tts_script": {
                    "text": content[:500] + "..." if len(content) > 500 else content,
                    "speed": "normal",
                    "pause_duration": 1.0
                },
                "visual_elements": {
                    "background_color": "#ffffff",
                    "text_color": "#333333",
                    "font_size": "medium",
                    "layout": "bullet-points",
                    "image_suggestions": []
                }
            }
        ],
        "metadata": {
            "created_timestamp": "2025-06-08",
            "total_duration_seconds": 150,
            "slide_count": 2,
            "content_source": "Fallback generated",
            "tts_voice_settings": {
                "voice_type": "vietnamese_female_teacher",
                "speech_rate": 1.0,
                "pitch": 0.0,
                "volume": 0.8
            }
        }
    }
