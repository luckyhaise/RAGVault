from uuid import UUID

from fastapi import APIRouter, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.upload_file_validation import validate_file
from app.api.dependencies.validate_token import validate_token_and_get_user_id
from app.db.database import get_db
from app.schemas.documents_schema import CreateDocumentsCommand, DeleteDocumentCommand, RetrieveAllUserDocuments, RetrieveAllUserDocumentsResponse, RetrieveDocument
from app.schemas.ingestion_jobs_schema import IngestionJobsResponse
from app.services.document.document_presistence_service import (
    delete_document_service,
    save_document_service,
)
from app.services.document.document_fetch_service import fetch_all_user_documents, get_user_document

document_router = APIRouter(tags=["document"],prefix="/document")
@document_router.post(path="/upload",response_model=IngestionJobsResponse)
async def save_document(user_id:UUID= Depends(validate_token_and_get_user_id),session:AsyncSession =Depends(get_db),validated_document:tuple[str,str]= Depends(validate_file) ,idempotency_key:UUID = Form(...)):
    original_file , title = validated_document
    
    command = CreateDocumentsCommand(user_id=user_id,title=title,original_text=original_file,idempotency_key=idempotency_key)

    return  await save_document_service(session=session,command=command)
    
@document_router.post(path="/delete",response_model=None)
async def delete_document(document_id:UUID,user_id:UUID = Depends(validate_token_and_get_user_id),session:AsyncSession = Depends(get_db)):
    command = DeleteDocumentCommand(user_id=user_id,id=document_id)
    return await delete_document_service(session=session,command=command)
    
@document_router.post(path="/get-all-documents",response_model=RetrieveAllUserDocumentsResponse)
async def get_all_documents(document_command:RetrieveAllUserDocuments,session:AsyncSession=Depends(get_db),user_id:UUID = Depends(validate_token_and_get_user_id)):
    
    return await fetch_all_user_documents(document_command=document_command,session=session,user_id=user_id)

@document_router.post(path="/get-document",response_model=None)
async def get_document(document_command:RetrieveDocument,session:AsyncSession=Depends(get_db),user_id:UUID=Depends(validate_token_and_get_user_id)):
    return await get_user_document(document_command=document_command,user_id=user_id,session=session)
