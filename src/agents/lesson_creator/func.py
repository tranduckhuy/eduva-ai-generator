from typing import TypedDict, Optional, List
from langchain_core.messages import AnyMessage, ToolMessage
from langgraph.graph.message import add_messages
from typing import Sequence, Annotated
from langchain_core.documents import Document
from .tools import retrieve_document
from src.utils.logger import logger

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
