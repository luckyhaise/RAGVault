from uuid import uuid4

import pytest
from account_helper import ensure_user

from app.core.exceptions.exceptions import NotFoundError
from app.services.injestion_job_service import (
    ingestion_job_success,
    start_ingestion_job,
)


@pytest.mark.asyncio
async def test_ingestion_job_success_marks_job_completed(db_session):
    user = await ensure_user(db_session)
    job = await start_ingestion_job(
        user_id=user.id,
        session=db_session,
        idempotency_key=uuid4(),
    )

    completed = await ingestion_job_success(job_id=job.id, session=db_session)

    assert completed.id == job.id
    assert completed.status == "completed"
    assert completed.completed_at is not None
    assert completed.error_message is None


@pytest.mark.asyncio
async def test_ingestion_job_success_raises_not_found_for_missing_job(
    db_session,
):
    missing_job_id = uuid4()

    with pytest.raises(NotFoundError) as excinfo:
        await ingestion_job_success(job_id=missing_job_id, session=db_session)

    assert excinfo.value.public_message == "Job dosen't exist"
    assert str(missing_job_id) in excinfo.value.internal_message
    assert excinfo.value.status_code == 404


@pytest.mark.asyncio
async def test_ingestion_job_success_accepts_custom_status(db_session):
    user = await ensure_user(db_session)
    job = await start_ingestion_job(
        user_id=user.id,
        session=db_session,
        idempotency_key=uuid4(),
    )

    completed = await ingestion_job_success(
        job_id=job.id,
        session=db_session,
        status="processing",
    )

    assert completed.status == "processing"
    assert completed.completed_at is not None
