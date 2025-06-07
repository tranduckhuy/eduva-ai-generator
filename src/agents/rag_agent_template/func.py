from typing import TypedDict, Optional, List
from langchain_core.messages import AnyMessage, ToolMessage
from langgraph.graph.message import add_messages
from typing import Sequence, Annotated
from langchain_core.messages import RemoveMessage
from langchain_core.documents import Document
from .tools import retrieve_document, python_repl, duckduckgo_search
from src.utils.logger import logger
from src.config.llm import get_llm
from .prompt import system_prompt, template_prompt

tools = [retrieve_document, python_repl, duckduckgo_search]


class State(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages]
    selected_ids: Optional[List[str]]
    selected_documents: Optional[List[Document]]


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
    tool_names = ["retrieve_document"]
    model_name = state.get("model_name", "gemini-2.0-flash")
    api_key = state.get("api_key", None)
    tool_name_to_func = {tool.name: tool for tool in tools}
    tool_functions = [
        tool_name_to_func[name] for name in tool_names if name in tool_name_to_func
    ]
    prompt = system_prompt
    print(f"tools: {tool_functions}")
    llm_call = template_prompt | get_llm(model_name, api_key).bind_tools(tool_functions)

    if tool_functions:
        for tool in tool_functions:
            if tool.name == "retrieve_document":
                prompt += "Sử dụng tool `retrieve_document` để truy xuất tài liệu của nhà trường để bổ sung thông tin cho câu trả lời"
            if tool.name == "python_repl":
                prompt += "Sử dụng tool `python_repl` để thực hiện các tác vụ liên quan đến tính toán phức tạp"
            if tool.name == "duckduckgo_search":
                prompt += "Sử dụng tool `duckduckgo_search` để tìm kiếm thông tin trên internet"

    response = await llm_call.ainvoke(
        {
            "system_prompt": prompt,
            "messages": messages,
        }
    )

    return {"messages": response}
