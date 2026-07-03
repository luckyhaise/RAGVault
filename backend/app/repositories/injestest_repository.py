from app.models.models import Ingestion_Jobs
from sqlalchemy.orm import Session 
from sqlalchemy import select
import logging
from datetime import datetime, UTC
from app.core.exceptions import NotFoundError
from uuid import UUID
from app.core.db_error_handle import run_database_operation

logger = logging.getLogger(__name__)

def start_ingestion_job(user_id:UUID,session:Session,document_id:UUID,idempotency_key:UUID,status:str = "processing"):
     def operation(): 
        stmt = select(Ingestion_Jobs).where(Ingestion_Jobs.user_id==user_id,Ingestion_Jobs.idempotency_key==idempotency_key)
        existing_job =  session.execute(stmt).scalars().first()
    
        if existing_job :
            logger.info("Ingestion job already exists | user_id=%s | idempotency_key=%s", user_id, idempotency_key)
            return existing_job
        job = Ingestion_Jobs(user_id=user_id,
                            document_id = document_id,
                            status=status,
                            idempotency_key = idempotency_key)
        

        session.add(job)
        session.commit()
        return job
     return run_database_operation(db=session,operation=operation)
    
def  ingestion_job_success(job_id:UUID,session:Session,status="completed"):
    def operation():
        job = session.get(Ingestion_Jobs,job_id)
        if not job:
            raise NotFoundError(f"No Job found with Job Id{job_id}",public_message="Job dosen't exist")
        job.status = status
        job.completed_at = datetime.now(UTC)
        session.commit()
        logger.info(
            "Ingestion job completed | job_id=%s | document_id=%s",
            job.id,
            job.document_id,
        )

        return job
    
    return run_database_operation(db=session,operation=operation)

def ingestion_job_failed(job_id:UUID,error_message:str,session:Session,status="failed"):
    def operation():
        job = session.get(Ingestion_Jobs,job_id)
        if not job:
            raise NotFoundError(f"No Job found with Job Id{job_id}",public_message="Job dosen't exist")
        job.status = status
        job.completed_at = datetime.now(UTC)
        job.error_message = error_message
        session.commit()
        logger.error(
        "Ingestion job failed | job_id=%s | document_id=%s | error_message=%s",
            job.id,
            job.document_id,
            error_message,
        )

        return job
    return run_database_operation(db=session,operation=operation)