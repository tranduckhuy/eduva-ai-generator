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
