from src.config.vector_store import vector_store
from typing import List
from fastapi import APIRouter, Query
from langchain_core.documents import Document
from pydantic import Field, BaseModel

router = APIRouter(prefix="/vector-store", tags=["Vector Store"])


@router.get("/get-documents")
async def get_documents():
    documents = await vector_store.get_documents()
    return [doc.__dict__ for doc in documents]


@router.get("/search")
async def search(query: str):
    documents = await vector_store.search(query)
    return [doc.__dict__ for doc in documents]


class AddDocumentsRequest(BaseModel):
    ids: List[str] = Field(..., description="The IDs of the documents")
    documents: List[Document] = Field(..., description="The documents")


@router.post("/add-documents")
async def add_documents(
    body: AddDocumentsRequest,
):
    await vector_store.add_documents(body.documents, ids=body.ids)
    return {"message": "Documents added successfully"}


@router.delete("/delete-documents")
async def delete_documents(ids: List[str] = Query(None)):
    all_docs = await vector_store.get_documents()
    all_ids = [doc.id for doc in all_docs]

    # Nếu không truyền ids thì xóa hết
    if not ids:
        ids = all_ids

    # Lọc ra những ID tồn tại
    delete_ids = [id for id in ids if id in all_ids]

    await vector_store.delete_documents(delete_ids)
    return {"deleted_ids": delete_ids}
