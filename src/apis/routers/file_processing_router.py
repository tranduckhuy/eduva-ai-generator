# src/api/routers/file_processing_router.py

from fastapi import APIRouter, status, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from src.utils.logger import logger
from src.config.vector_store import vector_store

import os
import tempfile
import shutil
import fitz  # PyMuPDF
from docx import Document as DocxDoc

# LangChain tools
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    Docx2txtLoader,
    UnstructuredFileLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

router = APIRouter(prefix="/file", tags=["File Processing"])


class FileIngressResponse(BaseModel):
    file_path: str = Field(..., title="Path to the processed file")
    chunks_count: int = Field(..., title="Number of chunks created")
    success: bool = Field(..., title="Whether the ingestion was successful")
    message: str = Field(
        "File processed and indexed successfully", title="Status message"
    )


@router.post("/analyze")
async def analyze_file(file: UploadFile = File(...)):
    try:
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, file.filename)

        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_extension = os.path.splitext(file.filename)[1].lower()
        file_type = file_extension.replace(".", "").upper()

        word_count = 0
        image_count = 0

        if file_extension == ".pdf":
            doc = fitz.open(temp_file_path)
            try:
                for page in doc:
                    text = page.get_text("text")
                    word_count += len(text.split())
                    image_count += len(page.get_images(full=True))
            finally:
                doc.close()  # Ensure the PDF is properly closed
        elif file_extension == ".docx":
            doc = DocxDoc(temp_file_path)
            for para in doc.paragraphs:
                word_count += len(para.text.split())
            for rel in doc.part._rels.values():
                if "image" in rel.target_ref:
                    image_count += 1
        else:
            shutil.rmtree(temp_dir)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": f"Unsupported file type: {file_extension}"},
            )

        shutil.rmtree(temp_dir)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "file_path": file.filename,
                "word_count": word_count,
                "image_count": image_count,
                "file_type": file_type,
            },
        )

    except Exception as e:
        logger.error(f"Error analyzing file: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Error analyzing file: {str(e)}"},
        )


@router.post("/ingress", response_model=FileIngressResponse)
async def ingress_file(file: UploadFile = File(...)):
    try:
        logger.info(f"Processing and indexing file: {file.filename}")

        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, file.filename)

        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Use appropriate loader
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension == ".pdf":
            loader = PyMuPDFLoader(temp_file_path)
        elif file_extension == ".docx":
            loader = Docx2txtLoader(temp_file_path)
        else:
            loader = UnstructuredFileLoader(temp_file_path)

        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(docs)

        # Add to vector store (async)
        await vector_store.add_documents(chunks)

        shutil.rmtree(temp_dir)
        chunks_count = len(chunks)

        return FileIngressResponse(
            file_path=file.filename,
            chunks_count=chunks_count,
            success=True,
            message=f"File processed and indexed successfully. Created {chunks_count} chunks.",
        )

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "file_path": file.filename if file else "unknown",
                "chunks_count": 0,
                "success": False,
                "message": f"Error processing file: {str(e)}",
            },
        )
