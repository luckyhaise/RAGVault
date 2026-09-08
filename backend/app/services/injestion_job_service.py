import logging
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.database_errors import translate_database_error
from app.core.exceptions.exceptions import NotFoundError
from app.repositories.ingestion_job_repository import (
    create,
    get_by_idempotency_key,
    get_by_job_id,
)

logger = logging.getLogger(__name__)

async def start_ingestion_job(user_id:UUID,session:AsyncSession,idempotency_key:UUID,status:str = "pending",document_id:UUID|None=None):
    try:
        existing_job = await get_by_idempotency_key(session=session,user_id=user_id,idempotency_key= idempotency_key)

        if existing_job :
            logger.info("Ingestion job already exists | user_id=%s | idempotency_key=%s", user_id, idempotency_key)
            return existing_job
        job = await create(session=session,user_id=user_id,document_id=document_id,idempotency_key=idempotency_key,status=status)
        logger.info("Ingestion job started | job_id=%s | user_id=%s | idempotency_key=%s", job.id, user_id, idempotency_key)
        return job
    except SQLAlchemyError as exc:
        await session.rollback()
        raise translate_database_error(exc=exc) from exc
    
async def  ingestion_job_success(job_id:UUID,session:AsyncSession,status:Literal['pending', 'completed', 'failed', 'processing'] ="completed"):
    try:
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
    except SQLAlchemyError as exc:
        await session.rollback()
        raise translate_database_error(exc=exc) from exc

async def ingestion_job_failed(job_id:UUID,error_message:str,session:AsyncSession,status:Literal['pending', 'completed', 'failed', 'processing']="failed"):
    try:
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
    except SQLAlchemyError as exc:
        await session.rollback()
        raise translate_database_error(exc=exc) from exc
