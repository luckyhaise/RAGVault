from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.database_errors import translate_database_error
from app.core.exceptions.exceptions import AppError
from app.repositories.chunks_repository import save_chunks
from app.repositories.documents_repository import create_document, delete_document
from app.schemas.documents_schema import CreateDocumentsCommand, DeleteDocumentCommand
from app.services.injestion_job_service import (
    ingestion_job_failed,
    ingestion_job_success,
    start_ingestion_job,
)
from app.utils.chunk_data import chuckey_chunkey


async def save_document_service(session:AsyncSession,command:CreateDocumentsCommand) :

    job = await start_ingestion_job(user_id=command.user_id,
                                   session=session,
                                   idempotency_key=command.idempotency_key)
    
    await session.commit()
    await session.refresh(job)
    job_id = job.id
    
  
    if job.document_id is not None :
       return {
            "id": job_id,
            "user_id": command.user_id,
            "document_id" : job.document_id ,
            "status":job.status,
            "completed_at": job.completed_at,
            "created_at":job.created_at,
            "idempotency_key" : job.idempotency_key,
            "updated_at" : job.updated_at
        }
    
    try :
        document = await create_document(user_id=command.user_id,
                                   session=session,
                                   title=command.title,
                                   original_text = command.original_text)
        
        job.document_id = document.id
   
        
        # chunking and rest of logic here
        chunks = chuckey_chunkey(document.original_text)
        _ = await save_chunks(document_id=document.id,chunks=chunks,session=session)
     
        
        




        _ =await ingestion_job_success(job_id=job_id , session= session)
        await session.commit() 
        await session.refresh(job)
        return {
            "id": job_id,
            "user_id": command.user_id,
            "document_id" : document.id ,
            "status":job.status,
            "completed_at": job.completed_at,
            "created_at":job.created_at,
            "idempotency_key" : job.idempotency_key,
            "updated_at" : job.updated_at
        }
    except Exception as exc:
       await  session.rollback()
       exc_error_code = "UNEXPECTED_DOCUMENT_SERVICE_ERROR"
       exc_public_message = "Document ingestion failed"
       internal_msg = str(exc)

       if isinstance(exc,SQLAlchemyError):
            error =  translate_database_error(exc=exc)
            internal_msg = str(error.internal_message)
            exc_error_code = str(error.error_code)
            exc_public_message = str(error.public_message)
       elif isinstance(exc,AppError):
           exc_error_code = exc.error_code
           exc_public_message = exc.public_message
           internal_msg = exc.internal_message
           
      
        
      
       job = await ingestion_job_failed(job_id=job_id,error_message=exc_public_message,session=session)
       await session.commit()
       await session.refresh(job)
       raise AppError(public_message=exc_public_message ,internal_message=internal_msg ,status_code=500, error_code=exc_error_code) from exc

async def delete_document_service(session:AsyncSession,command:DeleteDocumentCommand):
    try:
        title = await delete_document(session=session,
                            user_id=command.user_id,
                            document_id=command.id)
        await session.commit()
        return {
            "detail": f"{title} has been deleted"
           
       }
        
    except SQLAlchemyError as exc:
        await session.rollback()
        raise translate_database_error(exc=exc) from exc 
    
