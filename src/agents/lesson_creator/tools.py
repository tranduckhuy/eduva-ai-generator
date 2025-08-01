from langchain_core.tools import tool
from src.config.vector_store import vector_store
from src.utils.helper import convert_list_context_source_to_str
from src.utils.logger import logger

@tool
def retrieve_document(query: str) -> dict:
    """
    Retrieve relevant documents from the vector store based on the query.
    """
    # Build metadata filter
    metadata_filter = {}
    
    # Configure search kwargs with filter
    search_kwargs = {"k": 7, "score_threshold": 0.25}
    if metadata_filter:
        search_kwargs["filter"] = metadata_filter
    
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold", 
        search_kwargs=search_kwargs,
    )
    
    logger.info(f"Searching with query: '{query}', filter: {metadata_filter}")
    documents = retriever.invoke(query)
    
    # Keep original Document objects instead of converting to dict
    selected_documents = documents
    selected_ids = [doc.metadata.get("id", f"doc_{i}") for i, doc in enumerate(documents)]
    context_str = convert_list_context_source_to_str(documents)

    logger.info(f"Found {len(documents)} documents matching the criteria")

    return {
        "context_str": context_str,
        "selected_documents": selected_documents,
        "selected_ids": selected_ids,
    }
