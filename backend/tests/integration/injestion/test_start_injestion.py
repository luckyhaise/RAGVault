import pytest
from uuid import uuid4

from app.services.injestion_job_service import start_ingestion_job
from account_helper import ensure_user



@pytest.mark.asyncio
async def test_start_ingestion_job_creates_pending_job(db_session):
    user = await ensure_user(db_session)
    idempotency_key = uuid4()

    job = await start_ingestion_job(
        user_id=user.id,
        session=db_session,
        idempotency_key=idempotency_key,
    )

    assert job.id is not None
    assert job.user_id == user.id
    assert job.idempotency_key == idempotency_key
    assert job.status == "pending"
    assert job.document_id is None
    assert job.error_message is None
    assert job.completed_at is None


@pytest.mark.asyncio
async def test_start_ingestion_job_returns_existing_job_for_same_idempotency_key(
    db_session: db_session,
):
    user = await ensure_user(db_session)
    idempotency_key = uuid4()

    first = await start_ingestion_job(
        user_id=user.id,
        session=db_session,
        idempotency_key=idempotency_key,
    )
    second = await start_ingestion_job(
        user_id=user.id,
        session=db_session,
        idempotency_key=idempotency_key,
    )

    assert second.id == first.id
    assert second.idempotency_key == first.idempotency_key
    assert second.user_id == first.user_id
    assert second.status == first.status


@pytest.mark.asyncio
async def test_start_ingestion_job_creates_separate_jobs_for_different_keys(
    db_session: db_session,
):
    user = await ensure_user(db_session)
    key_one = uuid4()
    key_two = uuid4()

    job_one = await start_ingestion_job(
        user_id=user.id,
        session=db_session,
        idempotency_key=key_one,
    )
    job_two = await start_ingestion_job(
        user_id=user.id,
        session=db_session,
        idempotency_key=key_two,
        status="processing",
    )

    assert job_one.id != job_two.id
    assert job_one.idempotency_key == key_one
    assert job_two.idempotency_key == key_two
    assert job_one.status == "pending"
    assert job_two.status == "processing"
