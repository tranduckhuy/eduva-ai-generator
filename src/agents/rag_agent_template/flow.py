from langgraph.graph import StateGraph, START, END
from .func import (
    State,
    trim_history,
    execute_tool,
    generate_answer_rag,
    extract_slide_data,
)
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import InMemorySaver


class RAGAgentTemplate:
    def __init__(self):
        self.builder = StateGraph(State)

    @staticmethod
    def should_continue(state: State):
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "execute_tool"
        return "extract_slide_data"

    def node(self):
        self.builder.add_node("trim_history", trim_history)
        self.builder.add_node("generate_answer_rag", generate_answer_rag)
        self.builder.add_node("execute_tool", execute_tool)
        self.builder.add_node("extract_slide_data", self.extract_and_store_slide_data)

    def edge(self):
        self.builder.add_edge(START, "trim_history")
        self.builder.add_edge("trim_history", "generate_answer_rag")
        self.builder.add_conditional_edges(
            "generate_answer_rag",
            self.should_continue,
            {
                "extract_slide_data": "extract_slide_data",
                "execute_tool": "execute_tool",
            },
        )
        self.builder.add_edge("execute_tool", "generate_answer_rag")
        self.builder.add_edge("extract_slide_data", END)

    def extract_and_store_slide_data(self, state: State):
        """Extract structured slide data from AI response"""
        messages = state["messages"]
        last_message = messages[-1]

        # Extract slide data from the response
        slide_data = extract_slide_data(last_message.content)

        return {
            "slide_data": slide_data
        }

    def __call__(self) -> CompiledStateGraph:
        self.node()
        self.edge()

        return self.builder.compile(checkpointer=InMemorySaver())


rag_agent_template_agent = RAGAgentTemplate()()
