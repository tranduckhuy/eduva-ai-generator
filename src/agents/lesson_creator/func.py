from typing import TypedDict, Optional, List
from langchain_core.messages import AnyMessage, ToolMessage
from langgraph.graph.message import add_messages
from typing import Sequence, Annotated
from langchain_core.documents import Document
from .tools import retrieve_document
from src.utils.logger import logger
from src.config.llm import get_llm
from .prompt import system_prompt, template_prompt

tools = [retrieve_document]


class State(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages]
    selected_documents: Optional[List[Document]]
    slide_data: Optional[dict]


def execute_tool(state: State):
    """Execute RAG tool to retrieve relevant documents"""
    tool_calls = state["messages"][-1].tool_calls
    tool_messages = []
    selected_documents = []
    
    logger.info(f"execute_tool called with {len(tool_calls)} tool calls")
    
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]
        
        logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

        if tool_name == "retrieve_document":
            query = tool_args.get("query", "")
            logger.info(f"RAG Query: {query}")
            
            result = retrieve_document.invoke(query)
            context_str = result.get("context_str", "")
            selected_documents = result.get("selected_documents", [])
            
            logger.info(f"Retrieved {len(selected_documents)} documents")
            
            tool_messages.append(
                ToolMessage(
                    tool_call_id=tool_id,
                    content=context_str,
                )
            )

    return {
        "selected_documents": selected_documents,
        "messages": tool_messages,
    }


async def generate_slide_content(state: State):
    """Generate slide content using LLM with RAG context for high school students"""
    messages = state["messages"]
    
    # Use default LLM configuration for high school content
    from src.config.llm import llm_2_0
    llm_call = template_prompt | llm_2_0.bind_tools(tools)
    
    response = await llm_call.ainvoke({
        "system_prompt": system_prompt,
        "messages": messages,
    })
    
    return {"messages": response}


def create_slide_data(ai_response: str) -> dict:
    """Create structured slide data from AI response"""
    try:
        import json
        import re
        
        # Try to extract JSON from response
        json_pattern = r'\{[\s\S]*\}'
        json_match = re.search(json_pattern, ai_response)
        
        if json_match:
            slide_data = json.loads(json_match.group())
            return slide_data
        else:
            # Create basic slide structure if no JSON found
            return create_basic_slides(ai_response)
            
    except Exception as e:
        logger.error(f"Error creating slide data: {e}")
        return create_basic_slides(ai_response)


def create_basic_slides(content: str) -> dict:
    """Create basic slide structure"""
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
        "tts_script": f"Chào mừng các em đến với bài học: {title}",
        "image_keywords": ["education", "learning", "presentation"]
    })
    slide_id += 1
    
    # Content slides
    content_lines = lines[1:] if len(lines) > 1 else [content]
    for i, line in enumerate(content_lines[:5]):  # Max 5 content slides
        slides.append({
            "slide_id": slide_id,
            "type": "content", 
            "title": f"Nội dung {i + 1}",
            "content": [line],
            "tts_script": f"Bây giờ chúng ta tìm hiểu về: {line}",
            "image_keywords": ["diagram", "illustration", "concept"]
        })
        slide_id += 1
    
    return {
        "lesson_info": {
            "title": title,
            "slide_count": len(slides)
        },
        "slides": slides
    }
