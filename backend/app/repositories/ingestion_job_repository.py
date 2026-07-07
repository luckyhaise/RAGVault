from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Ingestion_Jobs
from uuid import UUID
async def get_by_idempotency_key(session:AsyncSession,user_id:UUID,idempotency_key:UUID):
    stmt = select(Ingestion_Jobs).where(Ingestion_Jobs.user_id == user_id,Ingestion_Jobs.idempotency_key == idempotency_key)
    result =  await session.execute(stmt)
    return result.scalar_one_or_none()

async def create(session:AsyncSession,user_id:UUID,idempotency_key:UUID ,status:str = "pending",document_id:UUID|None= None):
    job = Ingestion_Jobs(user_id = user_id , document_id = document_id,status = status,idempotency_key = idempotency_key)
    session.add(job)
    await session.flush()
    return job

async def get_by_job_id(job_id:UUID,session:AsyncSession):
    job = await session.get(Ingestion_Jobs,job_id)
    return job
