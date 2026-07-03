from fastapi import APIRouter
from .routes.document_router import document_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(document_router)