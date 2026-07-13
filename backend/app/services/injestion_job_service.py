from sqlalchemy.ext.asyncio import AsyncSession
import logging
from app.repositories.ingestion_job_repository import get_by_idempotency_key , create , get_by_job_id
from datetime import datetime, UTC
from app.core.exceptions.exceptions import NotFoundError
from uuid import UUID
from app.core.exceptions.database_errors import run_database_operation

logger = logging.getLogger(__name__)

async def start_ingestion_job(user_id:UUID,session:AsyncSession,idempotency_key:UUID,status:str = "pending",document_id:UUID|None=None):
     async def operation(): 
        
        existing_job = await get_by_idempotency_key(session=session,user_id=user_id,idempotency_key= idempotency_key)
    
        if existing_job :
            logger.info("Ingestion job already exists | user_id=%s | idempotency_key=%s", user_id, idempotency_key)
            return existing_job
        job = await create(session=session,user_id=user_id,document_id=document_id,idempotency_key=idempotency_key,status=status)
        return job
     return await run_database_operation(db=session,operation=operation)
    
async def  ingestion_job_success(job_id:UUID,session:AsyncSession,status="completed"):
    async def operation():
        job = await get_by_job_id(job_id=job_id,session=session)
        if not job:
            raise NotFoundError(f"No Job found with Job Id{job_id}",public_message="Job dosen't exist")
        job.status = status
        job.completed_at = datetime.now(UTC)
        await session.flush()
        logger.info(
            "Ingestion job completed | job_id=%s | document_id=%s",
            job.id,
            job.document_id,
        )

        return job
    
    return await run_database_operation(db=session,operation=operation)

async def ingestion_job_failed(job_id:UUID,error_message:str,session:AsyncSession,status="failed"):
    async def operation():
        job = await get_by_job_id(job_id=job_id,session=session)
        if not job:
            raise NotFoundError(f"No Job found with Job Id{job_id}",public_message="Job dosen't exist")
        job.status = status
        job.completed_at = datetime.now(UTC)
        job.error_message = error_message
        await session.flush()
        logger.error(
        "Ingestion job failed | job_id=%s | document_id=%s | error_message=%s",
            job.id,
            job.document_id,
            error_message,
        )

        return job
    return await run_database_operation(db=session,operation=operation)