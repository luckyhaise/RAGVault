from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.documents_schema import CreateDocumentsCommand, DeleteDocumentCommand
from app.core.exceptions.database_errors import translate_database_error , run_database_operation
from app.core.exceptions.exceptions import AppError
from sqlalchemy.exc import  SQLAlchemyError
from app.repositories.documents_repository import create_document , delete_document
from app.services.injestion_job_service import start_ingestion_job , ingestion_job_failed,ingestion_job_success
from app.utils.chunk_data import chuckey_chunkey
from app.repositories.chunks_repository import save_chunks
  
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
        await save_chunks(document_id=document.id,chunks=chunks,session=session)
     
        
        




        await ingestion_job_success(job_id=job_id , session= session)
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

       if isinstance(exc,SQLAlchemyError):
            error =  translate_database_error(exc=exc)
            exc = str(error.internal_message)
            exc_error_code = str(error.error_code)
            exc_public_message = str(error.public_message)
       elif isinstance(exc,AppError):
           exc_error_code = exc.error_code
           exc_public_message = exc.public_message
           exc = exc.internal_message
           
       else:
           
           exc = str(exc)
        
      
       job = await ingestion_job_failed(job_id=job_id,error_message=exc,session=session)
       await session.commit()
       await session.refresh(job)
       raise AppError(public_message=exc_public_message ,internal_message=exc ,status_code=500, error_code=exc_error_code)

async def delete_document_service(session:AsyncSession,command:DeleteDocumentCommand):
    async def operation():
        result = await delete_document(session=session,
                            user_id=command.user_id,
                            document_id=command.id)
        return result
     
    return await run_database_operation(session=session,operation=operation)
   
