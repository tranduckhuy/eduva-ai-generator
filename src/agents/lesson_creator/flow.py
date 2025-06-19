from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from .func import State, execute_tool, generate_slide_content, create_slide_data
from src.utils.logger import logger


def create_slide_workflow():
    """Create a simple workflow for slide generation with RAG"""

    def should_continue(state: State):
        """Decide whether to continue with tool execution or generate final result"""
        messages = state["messages"]
        last_message = messages[-1]

        # If last message has tool calls, execute them
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "execute_tool"
        # Otherwise, create slide data
        return "create_slides"

    def create_slides(state: State):
        """Create final slide data from AI response"""
        messages = state["messages"]
        last_message = messages[-1]

        if hasattr(last_message, "content"):
            slide_data = create_slide_data(last_message.content)
            logger.info(
                f"Created {slide_data.get('lesson_info', {}).get('slide_count', 0)} slides for high school students"
            )
            return {"slide_data": slide_data}

        return {"slide_data": None}

    # Build the workflow
    workflow = StateGraph(State)

    # Add nodes
    workflow.add_node("generate", generate_slide_content)
    workflow.add_node("execute_tool", execute_tool)
    workflow.add_node("create_slides", create_slides)

    # Add edges
    workflow.add_edge(START, "generate")
    workflow.add_conditional_edges(
        "generate",
        should_continue,
        {
            "execute_tool": "execute_tool",
            "create_slides": "create_slides",
        },
    )
    workflow.add_edge("execute_tool", "generate")
    workflow.add_edge("create_slides", END)

    return workflow.compile()


async def run_slide_creator(topic: str):
    """Run the slide creator workflow for high school students"""
    try:
        workflow = create_slide_workflow()

        initial_state = {
            "messages": [HumanMessage(content=topic)],
            "selected_documents": None,
            "slide_data": None,
        }

        logger.info(f"Starting high school slide creation for topic: {topic}")
        result = await workflow.ainvoke(initial_state)

        return {
            "success": True,
            "slide_data": result.get("slide_data"),
            "selected_documents": result.get("selected_documents", []),
        }

    except Exception as e:
        logger.error(f"Error in high school slide creation: {e}")
        return {"success": False, "error": str(e), "slide_data": None}
