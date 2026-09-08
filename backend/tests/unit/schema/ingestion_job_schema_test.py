from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.schemas.ingestion_jobs_schema import (
    Create_Ingestion_Jobs,
    Ingestion_Jobs_Response,
)

# from app.schemas.ingestion_job_schema import Create_Ingestion_Jobs, Ingestion_Jobs_Response


def make_response_data() -> dict:
    return {
        "id": uuid4(),
        "document_id": uuid4(),
        "user_id":uuid4(),
        "status": "pending",
        "error_message": None,
        "idempotency_key": uuid4(),
        "completed_at": None,
        "updated_at": datetime.now(UTC),
        "created_at": datetime.now(UTC),
    }




def test_create_ingestion_job_accepts_valid_data():
    user_id = uuid4()
    document_id = uuid4()

    job = Create_Ingestion_Jobs(
        user_id=user_id,
        document_id=document_id,
    )

    assert job.user_id == user_id
    assert job.document_id == document_id


@pytest.mark.parametrize(
    "missing_field",
    [
        "user_id",
        "document_id",
    ],
)
def test_create_ingestion_job_rejects_missing_required_fields(
    missing_field: str,
):
    data = {
        "user_id": uuid4(),
        "document_id": uuid4(),
    }

    data.pop(missing_field)

    with pytest.raises(ValidationError):
        Create_Ingestion_Jobs(**data)


@pytest.mark.parametrize(
    "field_name",
    [
        "user_id",
        "document_id",
    ],
)
def test_create_ingestion_job_rejects_invalid_uuids(
    field_name: str,
):
    data = {
        "user_id": uuid4(),
        "document_id": uuid4(),
    }

    data[field_name] = "not-a-valid-uuid"

    with pytest.raises(ValidationError):
        Create_Ingestion_Jobs(**data)



@pytest.mark.parametrize(
    "status",
    [
        "pending",
        "processing",
        "completed",
        "failed",
    ],
)
def test_ingestion_job_response_accepts_all_valid_statuses(
    status: str,
):
    data = make_response_data()
    data["status"] = status

    response = Ingestion_Jobs_Response(**data)

    assert response.status == status
    assert isinstance(response.id, UUID)
    assert isinstance(response.document_id, UUID)
    assert isinstance(response.idempotency_key, UUID)
    assert isinstance(response.created_at, datetime)
    assert isinstance(response.updated_at, datetime)


def test_ingestion_job_response_defaults_optional_fields_to_none():
    data = make_response_data()

    data.pop("document_id")
    data.pop("error_message")
    data.pop("completed_at")

    response = Ingestion_Jobs_Response(**data)

    assert response.document_id is None
    assert response.error_message is None
    assert response.completed_at is None


def test_completed_job_accepts_completion_time():
    completed_at = datetime.now(UTC)

    data = make_response_data()
    data["status"] = "completed"
    data["completed_at"] = completed_at

    response = Ingestion_Jobs_Response(**data)

    assert response.status == "completed"
    assert response.completed_at == completed_at


def test_failed_job_accepts_error_message():
    data = make_response_data()
    data["status"] = "failed"
    data["error_message"] = "Embedding generation failed"

    response = Ingestion_Jobs_Response(**data)

    assert response.status == "failed"
    assert response.error_message == "Embedding generation failed"


def test_ingestion_job_response_rejects_invalid_status():
    data = make_response_data()
    data["status"] = "cancelled"

    with pytest.raises(ValidationError):
        Ingestion_Jobs_Response(**data)


@pytest.mark.parametrize(
    "missing_field",
    [
        "id",
        "status",
        "idempotency_key",
        "updated_at",
        "created_at",
    ],
)
def test_ingestion_job_response_rejects_missing_required_fields(
    missing_field: str,
):
    data = make_response_data()
    data.pop(missing_field)

    with pytest.raises(ValidationError):
        Ingestion_Jobs_Response(**data)


@pytest.mark.parametrize(
    "field_name",
    [
        "id",
        "document_id",
        "idempotency_key",
    ],
)
def test_ingestion_job_response_rejects_invalid_uuids(
    field_name: str,
):
    data = make_response_data()
    data[field_name] = "not-a-valid-uuid"

    with pytest.raises(ValidationError):
        Ingestion_Jobs_Response(**data)


@pytest.mark.parametrize(
    "field_name",
    [
        "created_at",
        "updated_at",
        "completed_at",
    ],
)
def test_ingestion_job_response_rejects_invalid_datetimes(
    field_name: str,
):
    data = make_response_data()
    data[field_name] = "not-a-valid-datetime"

    with pytest.raises(ValidationError):
        Ingestion_Jobs_Response(**data)