from langchain_core.documents import Document
from typing import Union, TypedDict, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda
from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage
import base64
from fastapi import UploadFile
from typing import TypeVar

State = TypeVar("State", bound=Dict[str, Any])

def convert_list_context_source_to_str(contexts: list[Document]):
    formatted_str = ""
    for i, context in enumerate(contexts):
        formatted_str += f"Document index {i}:\nContent: {context.page_content}\n"
        formatted_str += "----------------------------------------------\n\n"
    return formatted_str
