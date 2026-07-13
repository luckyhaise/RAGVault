from fastapi import APIRouter
from .routes.document_router import document_router
from .routes.users_router import user_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(document_router)
api_router.include_router(user_router)
