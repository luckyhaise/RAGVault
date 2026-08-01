from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.documents_schema import CreateDocumentsCommand, DeleteDocumentCommand
from app.core.exceptions.database_errors import translate_database_error
from app.core.exceptions.exceptions import AppError
from sqlalchemy.exc import  SQLAlchemyError
from app.repositories.documents_repository import create_document , delete_document
from app.services.injestion_job_service import start_ingestion_job , ingestion_job_failed,ingestion_job_success
from app.utils.chunk_data import chuckey_chunkey
from app.repositories.chunks_repository import save_chunks
  
async def save_document_service(session:AsyncSession,command:CreateDocumentsCommand):

    job = await start_ingestion_job(user_id=command.user_id,
                                   session=session,
                                   idempotency_key=command.idempotency_key)
    
    await session.commit()
    await session.refresh(job)
    job_id = job.id
    
    if job.document_id is not None :
       return {
            "id": job_id,
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
            "document_id" : document.id ,
            "status":job.status,
            "completed_at": job.completed_at,
            "created_at":job.created_at,
            "idempotency_key" : job.idempotency_key,
            "updated_at" : job.updated_at
        }
    except Exception as exc:
       await  session.rollback()
   

       if isinstance(exc,SQLAlchemyError):
            error =  translate_database_error(exc=exc)
            exc = str(error.internal_message)
       else:
           exc = str(exc)
      
       job = await ingestion_job_failed(job_id=job_id,error_message=exc,session=session)
       await session.commit()
       await session.refresh(job)
       raise AppError(public_message="Document ingestion failed",internal_message=exc , status_code=500)

async def delete_document_service(session:AsyncSession,command:DeleteDocumentCommand):
    try:
     await delete_document(session=session,
                           user_id=command.user_id,
                           document_id=command.id)
    except Exception as exc:
        if isinstance(exc,SQLAlchemyError):
            error = translate_database_error(exc=exc)
            exc = error.internal_message
        else:
            exc = str(exc)
        raise AppError(public_message="Failed to delete the file",status_code=500,internal_message=exc)
