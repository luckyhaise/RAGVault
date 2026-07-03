from fastapi import APIRouter , UploadFile , Depends , File, Form, HTTPException , status 
from uuid import UUID
from pydantic import ValidationError
from sqlalchemy.orm import Session  
from sqlalchemy.exc import SQLAlchemyError
from app.utils.chunk_test import chuckey_chunkey
from app.schemas.injestion_jobs_schema import Ingestion_Jobs_Response
from app.schemas.documents_schema import Create_Documents
from app.core.db_error_handle import translate_database_error
from app.models.models import Documents , Documents_Chunks
from app.repositories.injestest_repository import start_ingestion_job,ingestion_job_failed,ingestion_job_success
from app.db.database import db 
document_router = APIRouter(tags=["document"],prefix="/document")

@document_router.post(path="/save_document",response_model=Ingestion_Jobs_Response)
async def save_document(user_id:UUID= Form(),session:Session =Depends(db),document_file:UploadFile = File(...),idempotency_key:UUID = Form(...)):
    allowed_text_types = {
    "text/plain",
    "text/csv",
    "text/markdown",
 }
    if document_file.content_type not in allowed_text_types:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,detail="Only .txt .csv .md files are allowed")
    
    file_bytes = await document_file.read()
    
    try:
        original_file = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Invaild text encoding")
    
    file_name = document_file.filename or "untitled_document"

    try:
        document_data = Create_Documents(user_id=user_id,title=file_name,original_text=original_file)
    except ValidationError as e :
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,detail=f"Validation Failed: {str(e)}")

    document = Documents(**document_data.model_dump())
    session.add(document)
    session.flush()
    job =  start_ingestion_job(user_id=user_id,session=session,document_id=document.id,idempotency_key=idempotency_key)

    try :
        session.commit()
        # chunking and rest of logic here
        chunks = chuckey_chunkey(original_file)
        for i, chunk in enumerate(chunks):
         document_chuncks = Documents_Chunks(chunk_index =i,document_id = document.id, content = chunk)
         session.add(document_chuncks)
        
        session.commit()
        session.refresh(document_chuncks)




        ingestion_job_success(job_id=job.id , session= session)
        return {
            "id": job.id,
            "status":job.status,
            "completed_at": job.completed_at,
            "created_at":job.created_at,
            "idempotency_key" : job.idempotency_key,
            "updated_at" : job.updated_at
        }
    except Exception as exc:
       if isinstance(exc,SQLAlchemyError):
            error =  translate_database_error(exc=exc)
            exc = error.internal_message
       job =  ingestion_job_failed(job_id=job.id,error_message=str(exc),session=session)
       return {
            "id": job.id,
            "status":job.status,
            "completed_at": job.completed_at,
            "error_message" : job.error_message,
            "created_at":job.created_at,
            "idempotency_key" : job.idempotency_key,
            "updated_at" : job.updated_at
        }


  


    

