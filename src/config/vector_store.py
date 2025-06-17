import os
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from typing import List, Dict, Any, Optional
from .llm import embeddings  # GoogleGenerativeAIEmbeddings instance

# Load from environment
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "eduva")

class PineconeVectorStoreCRUD:
    def __init__(
        self,
        index_name: str,
        embedding,
        pinecone_api_key: str,
        k: int = 5,
        score_threshold: float = 0.3,
    ):
        self.vector_store = PineconeVectorStore(
            index_name=index_name,
            embedding=embedding,
            pinecone_api_key=pinecone_api_key,
        )
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": k, "score_threshold": score_threshold},
        )

    def as_retriever(self, search_type: str = "similarity_score_threshold", search_kwargs: Optional[Dict[str, Any]] = None):
        """Return a retriever with custom search parameters"""
        if search_kwargs is None:
            search_kwargs = {"k": 5, "score_threshold": 0.3}
        
        return self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs,
        )

    async def search(self, query: str, filter: Optional[Dict[str, Any]] = None):
        return await self.retriever.ainvoke(query, filter=filter)

    async def add_documents(self, documents: List[Document], ids: Optional[List[str]] = None):
        await self.vector_store.aadd_documents(documents, ids=ids)

    async def get_documents(self, filter: Optional[Dict[str, Any]] = None):
        return await self.vector_store.asimilarity_search("", filter=filter)

    async def delete_documents(self, ids: List[str]):
        await self.vector_store.adelete(ids=ids)

    async def update_documents(self, documents: List[Document], ids: Optional[List[str]] = None):
        await self.vector_store.aadd_documents(documents, ids=ids)


# Singleton instance to use in routers/services
vector_store = PineconeVectorStoreCRUD(
    index_name=PINECONE_INDEX_NAME,
    embedding=embeddings,
    pinecone_api_key=PINECONE_API_KEY,
)
