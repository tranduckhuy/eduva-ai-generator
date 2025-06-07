from src.config.vector_store import vector_store
from typing import List
from fastapi import APIRouter, Query
from langchain_core.documents import Document
from pydantic import Field, BaseModel

router = APIRouter(prefix="/vector-store", tags=["Vector Store"])


@router.get("/get-documents")
async def get_documents():
    documents = await vector_store.asimilarity_search("", 10000)
    return [doc.__dict__ for doc in documents]


@router.get("/search")
async def search(query: str):
    documents = await vector_store.asimilarity_search(query, 5)
    return [doc.__dict__ for doc in documents]


class AddDocumentsRequest(BaseModel):
    ids: List[str] = Field(..., description="The IDs of the documents")
    documents: List[Document] = Field(..., description="The documents")


@router.post("/add-documents")
async def add_documents(
    body: AddDocumentsRequest,
):
    return await vector_store.aadd_documents(body.documents, ids=body.ids)


@router.delete("/delete-documents")
async def delete_documents(ids: List[str] = Query(None)):
    document_data = await vector_store.asimilarity_search("", 10000)
    document_ids = [doc.id for doc in document_data]
    if not ids:
        ids = document_ids
    delete_ids = [id for id in ids if id in document_ids]
    return await vector_store.adelete(ids=delete_ids)
