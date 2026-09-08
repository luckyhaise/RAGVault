from io import BytesIO
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.core.exceptions.exceptions import AppError

CREATE_URL = "/api/v1/user/create"
LOGIN_URL = "/api/v1/user/login"
UPLOAD_URL = "/api/v1/document/document/upload"


def _unique_user(**overrides) -> dict:
    suffix = uuid4().hex[:8]
    user = {
        "user_name": f"doc_user_{suffix}",
        "phone": f"+1{uuid4().int % 10**10:010d}",
        "email": f"doc_{suffix}@example.com",
        "name": "Doc Tester",
        "password": "Doc@pass12",
    }
    user.update(overrides)
    return user


async def _register_and_login(client: AsyncClient) -> str:
    user = _unique_user()
    created = await client.post(CREATE_URL, json=user)
    assert created.status_code == 200
    login = await client.post(
        LOGIN_URL,
        json={"user_name": user["user_name"], "password": user["password"]},
    )
    assert login.status_code == 200
    return login.json()


def _txt_files(content: bytes = b"hello route upload", filename: str = "note.txt"):
    return {"text_file": (filename, BytesIO(content), "text/plain")}


@pytest.mark.asyncio
async def test_upload_document_happy_path(client: AsyncClient):
    token = await _register_and_login(client)
    key = str(uuid4())

    response = await client.post(
        UPLOAD_URL,
        headers={"Authorization": f"Bearer {token}"},
        data={"idempotency_key": key},
        files=_txt_files(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["document_id"] is not None
    assert body["idempotency_key"] == key
    assert body["id"] is not None


@pytest.mark.asyncio
async def test_upload_document_idempotent_for_same_key(client: AsyncClient):
    token = await _register_and_login(client)
    key = str(uuid4())
    headers = {"Authorization": f"Bearer {token}"}

    first = await client.post(
        UPLOAD_URL,
        headers=headers,
        data={"idempotency_key": key},
        files=_txt_files(b"first upload body"),
    )
    second = await client.post(
        UPLOAD_URL,
        headers=headers,
        data={"idempotency_key": key},
        files=_txt_files(b"second upload body"),
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["document_id"] == second.json()["document_id"]


@pytest.mark.asyncio
async def test_upload_document_rejects_missing_auth(client: AsyncClient):
    response = await client.post(
        UPLOAD_URL,
        data={"idempotency_key": str(uuid4())},
        files=_txt_files(),
    )

    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_upload_document_rejects_invalid_auth(client: AsyncClient):
    response = await client.post(
        UPLOAD_URL,
        headers={"Authorization": "Bearer not-a-real-token"},
        data={"idempotency_key": str(uuid4())},
        files=_txt_files(),
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "http_error"


@pytest.mark.asyncio
async def test_upload_document_rejects_missing_idempotency_key(client: AsyncClient):
    token = await _register_and_login(client)

    response = await client.post(
        UPLOAD_URL,
        headers={"Authorization": f"Bearer {token}"},
        files=_txt_files(),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.asyncio
async def test_upload_document_rejects_bad_file_type(client: AsyncClient):
    token = await _register_and_login(client)

    response = await client.post(
        UPLOAD_URL,
        headers={"Authorization": f"Bearer {token}"},
        data={"idempotency_key": str(uuid4())},
        files={"text_file": ("note.pdf", BytesIO(b"%PDF-fake"), "application/pdf")},
    )

    assert response.status_code == 415
    assert response.json()["error"]["message"] == "Only .txt , .csv , .md files are allowed"


@pytest.mark.asyncio
async def test_upload_document_rejects_file_too_large(client: AsyncClient):
    token = await _register_and_login(client)

    with patch("app.api.dependencies.upload_file_validation.MAX_FILE_SIZE", 10):
        response = await client.post(
            UPLOAD_URL,
            headers={"Authorization": f"Bearer {token}"},
            data={"idempotency_key": str(uuid4())},
            files=_txt_files(b"x" * 20),
        )

    assert response.status_code == 413
    assert response.json()["error"]["message"] == "File size should be with 50 MB"


@pytest.mark.asyncio
async def test_upload_document_rejects_bad_encoding(client: AsyncClient):
    token = await _register_and_login(client)

    response = await client.post(
        UPLOAD_URL,
        headers={"Authorization": f"Bearer {token}"},
        data={"idempotency_key": str(uuid4())},
        files={"text_file": ("bad.txt", BytesIO(b"\xff\xfe\xfa"), "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["message"] == "Invalid text encoding"


@pytest.mark.asyncio
async def test_upload_document_ingestion_failure_returns_error(client: AsyncClient):
    token = await _register_and_login(client)
    failure = AppError(
        public_message="Document ingestion failed",
        internal_message="forced failure",
        status_code=500,
        error_code="SQL_ALCHEMY_ERROR",
    )

    with patch(
        "app.api.routes.document_router.save_document_service",
        new_callable=AsyncMock,
        side_effect=failure,
    ):
        response = await client.post(
            UPLOAD_URL,
            headers={"Authorization": f"Bearer {token}"},
            data={"idempotency_key": str(uuid4())},
            files=_txt_files(),
        )

    assert response.status_code == 500
    body = response.json()["error"]
    assert body["error_code"] == "SQL_ALCHEMY_ERROR"
    assert body["message"] == "Document ingestion failed"
