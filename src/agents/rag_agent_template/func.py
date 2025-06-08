from typing import TypedDict, Optional, List
from langchain_core.messages import AnyMessage, ToolMessage
from langgraph.graph.message import add_messages
from typing import Sequence, Annotated
from langchain_core.messages import RemoveMessage
from langchain_core.documents import Document
from .tools import retrieve_document, create_slide_content, python_repl, duckduckgo_search
from src.utils.logger import logger
from src.config.llm import get_llm
from .prompt import system_prompt, template_prompt
import json

tools = [retrieve_document, create_slide_content, python_repl, duckduckgo_search]


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
    tool_names = ["retrieve_document", "create_slide_content"]
    model_name = state.get("model_name", "gemini-2.0-flash")
    api_key = state.get("api_key", None)
    tool_name_to_func = {tool.name: tool for tool in tools}
    tool_functions = [
        tool_name_to_func[name] for name in tool_names if name in tool_name_to_func
    ]
    
    # Enhanced prompt for structured output
    enhanced_prompt = system_prompt + """

## **QUAN TRỌNG: Format đầu ra cho Pipeline tự động tạo Video**

Khi tạo bài giảng, bạn PHẢI trả về nội dung theo format JSON chuẩn để hệ thống có thể:
1. Tự động tạo slide với RevealJS
2. Sinh audio với TTS (Text-to-Speech)
3. Kết hợp thành video hoàn chỉnh

### **Format JSON yêu cầu:**

```json
{
  "lesson_info": {
    "title": "Tiêu đề bài giảng",
    "subject": "Môn học",
    "grade": "Lớp",
    "duration_minutes": 25,
    "total_slides": 8
  },
  "slides": [
    {
      "slide_number": 1,
      "type": "title",
      "title": "Tiêu đề slide",
      "content": "Nội dung hiển thị trên slide",
      "speaker_notes": "Script đầy đủ cho TTS - những gì giáo viên sẽ nói",
      "visual_elements": {
        "background_color": "#ffffff",
        "text_size": "large",
        "animations": ["fadeIn"],
        "images": ["mô tả hình ảnh cần có"],
        "charts": ["mô tả biểu đồ nếu cần"]
      },
      "duration_seconds": 30
    }
  ],
  "tts_settings": {
    "voice_type": "female",
    "speed": "normal",
    "language": "vi-VN"
  },
  "video_settings": {
    "resolution": "1920x1080",
    "fps": 30,
    "transition_effects": ["slide", "fade"]
  }
}
```

### **Các loại slide và format:**

1. **Title slide** (slide đầu):
   - type: "title"
   - Có logo, tiêu đề bài, thông tin môn học

2. **Content slide** (slide nội dung):
   - type: "content"
   - Bullet points rõ ràng, dễ đọc
   - Script chi tiết cho TTS

3. **Example slide** (slide ví dụ):
   - type: "example"
   - Ví dụ cụ thể, có thể có hình ảnh

4. **Summary slide** (slide tóm tắt):
   - type: "summary"
   - Điểm chính của bài học

### **Yêu cầu về nội dung:**

- **content**: Nội dung ngắn gọn hiển thị trên slide (bullet points)
- **speaker_notes**: Script đầy đủ, tự nhiên cho TTS (200-300 từ/slide)
- **visual_elements**: Mô tả chi tiết về hình ảnh, màu sắc, animation
- **duration_seconds**: Thời gian ước tính cho mỗi slide

Hãy LUÔN trả về format JSON này sau khi tạo xong bài giảng!
"""
    
    llm_call = template_prompt | get_llm(model_name, api_key).bind_tools(tool_functions)

    if tool_functions:
        for tool in tool_functions:
            if tool.name == "retrieve_document":
                enhanced_prompt += "\n\nSử dụng tool `retrieve_document` để tìm kiếm tài liệu giáo dục, sau đó kết hợp với yêu cầu của giáo viên để tạo nội dung slide phù hợp"
            if tool.name == "create_slide_content":
                enhanced_prompt += "\n\nSử dụng tool `create_slide_content` để tạo cấu trúc slide cơ bản, sau đó format thành JSON theo yêu cầu"

    response = await llm_call.ainvoke(
        {
            "system_prompt": enhanced_prompt,
            "messages": messages,
        }
    )

    return {"messages": response}


def extract_slide_data(content: str) -> dict:
    """
    Extract structured slide data from AI response
    """
    try:
        # Try to find JSON in the response
        import re
        json_pattern = r'\{[\s\S]*\}'
        json_match = re.search(json_pattern, content)
        
        if json_match:
            json_str = json_match.group()
            slide_data = json.loads(json_str)
            return slide_data
        else:
            # Fallback: parse text format and convert to JSON
            return parse_text_to_slide_data(content)
            
    except Exception as e:
        logger.error(f"Error extracting slide data: {e}")
        return create_fallback_slide_data(content)


def parse_text_to_slide_data(content: str) -> dict:
    """
    Parse text format response and convert to structured slide data
    """
    lines = content.split('\n')
    slides = []
    current_slide = None
    slide_number = 0
    
    for line in lines:
        line = line.strip()
        if 'SLIDE' in line.upper() and any(char.isdigit() for char in line):
            if current_slide:
                slides.append(current_slide)
            
            slide_number += 1
            current_slide = {
                "slide_number": slide_number,
                "type": "content",
                "title": line,
                "content": "",
                "speaker_notes": "",
                "visual_elements": {
                    "background_color": "#ffffff",
                    "text_size": "medium",
                    "animations": ["fadeIn"],
                    "images": [],
                    "charts": []
                },
                "duration_seconds": 45
            }
        elif current_slide and line:
            if len(current_slide["content"]) < 200:
                current_slide["content"] += line + "\n"
            current_slide["speaker_notes"] += line + " "
    
    if current_slide:
        slides.append(current_slide)
    
    return {
        "lesson_info": {
            "title": "Bài giảng",
            "subject": "Chưa xác định",
            "grade": "Cấp 3",
            "duration_minutes": len(slides) * 2,
            "total_slides": len(slides)
        },
        "slides": slides,
        "tts_settings": {
            "voice_type": "female",
            "speed": "normal",
            "language": "vi-VN"
        },
        "video_settings": {
            "resolution": "1920x1080",
            "fps": 30,
            "transition_effects": ["slide", "fade"]
        }
    }


def create_fallback_slide_data(content: str) -> dict:
    """
    Create basic slide data when parsing fails
    """
    return {
        "lesson_info": {
            "title": "Bài giảng",
            "subject": "Chưa xác định", 
            "grade": "Cấp 3",
            "duration_minutes": 10,
            "total_slides": 1
        },
        "slides": [
            {
                "slide_number": 1,
                "type": "content",
                "title": "Nội dung bài giảng",
                "content": content[:300] + "..." if len(content) > 300 else content,
                "speaker_notes": content,
                "visual_elements": {
                    "background_color": "#ffffff",
                    "text_size": "medium",
                    "animations": ["fadeIn"],
                    "images": [],
                    "charts": []
                },
                "duration_seconds": 60
            }
        ],
        "tts_settings": {
            "voice_type": "female",
            "speed": "normal",
            "language": "vi-VN"
        },
        "video_settings": {
            "resolution": "1920x1080",
            "fps": 30,
            "transition_effects": ["slide"]
        }
    }
