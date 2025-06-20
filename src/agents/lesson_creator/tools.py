from langchain_core.tools import tool
from src.config.vector_store import vector_store
from src.utils.helper import convert_list_context_source_to_str
from src.utils.logger import logger

@tool
def retrieve_document(query: str):
    """
    Truy xuất tài liệu giáo dục từ kho vector của nhà trường dựa trên nội dung truy vấn (chủ đề, môn học...).
    """
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 5, "score_threshold": 0.25},
    )
    documents = retriever.invoke(query)
    # Keep original Document objects instead of converting to dict
    selected_documents = documents  # Changed this line
    selected_ids = [doc.metadata.get("id", f"doc_{i}") for i, doc in enumerate(documents)]
    context_str = convert_list_context_source_to_str(documents)

    return {
        "context_str": context_str,
        "selected_documents": selected_documents,
        "selected_ids": selected_ids,
    }
