from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.documents_schema import CreateDocumentsCommand
from backend.app.core.exceptions.database_errors import translate_database_error
from sqlalchemy.exc import  SQLAlchemyError
from app.repositories.documents_repository import create_document
from app.services.ingestion_job_service import start_ingestion_job , ingestion_job_failed,ingestion_job_success
from app.utils.chunk_test import chuckey_chunkey
from app.repositories.chunks_repository import save_chunks
  
async def save_document_service(session:AsyncSession,command:CreateDocumentsCommand):

    job = await start_ingestion_job(user_id=command.user_id,
                                   session=session,
                                   idempotency_key=command.idempotency_key)
    await session.commit()
    await session.refresh(job)
    
    try :
        document = create_document(user_id=command.user_id,
                                   session=session,
                                   title=command.title,
                                   original_text = command.original_text)
        
        job.document_id = document.id
   
        
        # chunking and rest of logic here
        chunks = chuckey_chunkey(document.original_text)
        save_chunks(document_id=document.id,chunks=chunks,session=session)
     
        
        




        await ingestion_job_success(job_id=job.id , session= session)
        await session.commit() 
        await session.refresh(job)
        return {
            "id": job.id,
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
      
       
       if job is None:
           return{
            "id": None,
            "status":"failed",
            "completed_at": None,
            "error_message" :exc ,
            "created_at":None,
            "idempotency_key" : command.idempotency_key,
            "updated_at" : None,
               
           }
       job = await ingestion_job_failed(job_id=job.id,error_message=exc,session=session)
       await session.commit()
       await session.refresh(job)
       return {
            "id": job.id,
            "status":job.status,
            "completed_at": job.completed_at,
            "error_message" : job.error_message,
            "created_at":job.created_at,
            "idempotency_key" : job.idempotency_key,
            "updated_at" : job.updated_at
        }