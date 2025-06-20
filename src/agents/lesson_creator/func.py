from typing import TypedDict, Optional, List
from langchain_core.messages import AnyMessage, ToolMessage
from langgraph.graph.message import add_messages
from typing import Sequence, Annotated
from langchain_core.documents import Document
from .tools import retrieve_document
from src.utils.logger import logger
from .prompt import system_prompt, create_prompt_messages

tools = [retrieve_document]


class State(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages]
    selected_documents: Optional[List[Document]]
    slide_data: Optional[dict]
    uploaded_files_content: Optional[str]


def execute_tool(state: State):
    """Execute RAG tool to retrieve relevant documents - simplified"""
    messages = state.get("messages", [])
    if not messages:
        return {"selected_documents": [], "messages": []}
    
    last_message = messages[-1]
    tool_calls = getattr(last_message, 'tool_calls', None)
    
    if not tool_calls:
        return {"selected_documents": [], "messages": []}
    
    tool_messages = []
    selected_documents = []
    
    for tool_call in tool_calls:
        try:
            tool_name = tool_call.get("name", "")
            tool_args = tool_call.get("args", {})
            tool_id = tool_call.get("id", "")
            
            if tool_name == "retrieve_document":
                query = tool_args.get("query", "")
                result = retrieve_document.invoke(query)
                context_str = result.get("context_str", "")
                doc_list = result.get("selected_documents", [])
                
                if doc_list:
                    selected_documents.extend(doc_list)
                
                tool_messages.append(
                    ToolMessage(tool_call_id=tool_id, content=context_str)
                )
        except Exception as e:
            logger.error(f"Error executing tool: {e}")

    return {
        "selected_documents": selected_documents,
        "messages": tool_messages,
    }


async def generate_slide_content(state: State):
    """Generate slide content using LLM"""
    messages = state["messages"]
    prompt_messages = create_prompt_messages(system_prompt, messages)
    
    from src.config.llm import llm_2_0
    response = await llm_2_0.ainvoke(prompt_messages)
    
    return {"messages": [response]}


def create_slide_data(ai_response: str) -> dict:
    """Create structured slide data from AI response"""
    try:
        import json
        import re
        
        # Extract JSON from response
        json_pattern = r'\{[\s\S]*\}'
        json_match = re.search(json_pattern, ai_response)
        
        if json_match:
            slide_data = json.loads(json_match.group())
            return slide_data
        else:
            return create_basic_slides(ai_response)
            
    except Exception as e:
        logger.error(f"Error creating slide data: {e}")
        return create_basic_slides(ai_response)


def create_basic_slides(content: str) -> dict:
    """Create basic slide structure when JSON parsing fails"""
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
        "tts_script": f"Chào mừng các em đến với bài học về {title}",
        "image_keywords": ["education", "learning", "classroom", "students"],
        "estimated_duration_seconds": 90
    })
    slide_id += 1
    
    # Content slides
    content_lines = lines[1:] if len(lines) > 1 else [content]
    for i, line in enumerate(content_lines[:5]):
        slides.append({
            "slide_id": slide_id,
            "type": "content", 
            "title": f"Nội dung {i + 1}",
            "content": [line],
            "tts_script": f"Chúng ta tìm hiểu về {line}. Đây là kiến thức quan trọng các em cần nắm vững.",
            "image_keywords": ["education", "textbook", "learning", "diagram"],
            "estimated_duration_seconds": 120
        })
        slide_id += 1
    
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
