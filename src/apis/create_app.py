from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from src.apis.routers.lesson_creator_router import router as router_rag_agent_template
from src.apis.routers.file_processing_router import router as router_file_processing
from src.apis.routers.vector_store_router import router as vector_store_router


api_router = APIRouter()
api_router.include_router(router_rag_agent_template)
api_router.include_router(router_file_processing)
api_router.include_router(vector_store_router)


def create_app():
    app = FastAPI(
        docs_url="/swagger",
        title="AI Service",
    )

    @app.get("/")
    def root():
        return {
            "message": "Backend is running.",

        }

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
