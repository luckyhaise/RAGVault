import pytest
from uuid import uuid4

from app.core.exceptions.exceptions import NotFoundError
from app.services.injestion_job_service import (
    start_ingestion_job,
    ingestion_job_failed,
)
from app.services.user_services import (
    create_account_service,
    find_user_by_user_name,
    User_Create,
)
from conftest import db_session,  ensure_user




@pytest.mark.asyncio
async def test_ingestion_job_failed_marks_job_failed_with_error(db_session: db_session):
    user = await ensure_user(db_session)
    job = await start_ingestion_job(
        user_id=user.id,
        session=db_session,
        idempotency_key=uuid4(),
    )
    error_message = "Embedding generation failed"

    failed = await ingestion_job_failed(
        job_id=job.id,
        error_message=error_message,
        session=db_session,
    )

    assert failed.id == job.id
    assert failed.status == "failed"
    assert failed.error_message == error_message
    assert failed.completed_at is not None


@pytest.mark.asyncio
async def test_ingestion_job_failed_raises_not_found_for_missing_job(
    db_session: db_session,
):
    missing_job_id = uuid4()

    with pytest.raises(NotFoundError) as excinfo:
        await ingestion_job_failed(
            job_id=missing_job_id,
            error_message="something went wrong",
            session=db_session,
        )

    assert excinfo.value.public_message == "Job dosen't exist"
    assert str(missing_job_id) in excinfo.value.internal_message
    assert excinfo.value.status_code == 404


@pytest.mark.asyncio
async def test_ingestion_job_failed_accepts_custom_status(db_session: db_session):
    user = await ensure_user(db_session)
    job = await start_ingestion_job(
        user_id=user.id,
        session=db_session,
        idempotency_key=uuid4(),
    )

    failed = await ingestion_job_failed(
        job_id=job.id,
        error_message="chunking failed",
        session=db_session,
        status="processing",
    )

    assert failed.status == "processing"
    assert failed.error_message == "chunking failed"
    assert failed.completed_at is not None
