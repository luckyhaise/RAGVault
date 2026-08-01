from app.schemas.documents_schema import CreateDocumentsCommand , Create_Documents_Chunks , DeleteDocumentCommand , Retrieve_Document , Retrieve_Chunks 

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError




def test_create_document_command_accepts_valid_data():
    user_id = uuid4()
    idempotency_key = uuid4()

    command = CreateDocumentsCommand(
        user_id=user_id,
        title="Test document",
        original_text="This is the document content.",
        idempotency_key=idempotency_key,
    )

    assert command.user_id == user_id
    assert command.title == "Test document"
    assert command.original_text == "This is the document content."
    assert command.idempotency_key == idempotency_key


def test_create_document_command_rejects_empty_title():
    with pytest.raises(ValidationError):
        CreateDocumentsCommand(
            user_id=uuid4(),
            title="",
            original_text="Valid document content",
            idempotency_key=uuid4(),
        )


def test_create_document_command_rejects_empty_original_text():
    with pytest.raises(ValidationError):
        CreateDocumentsCommand(
            user_id=uuid4(),
            title="Valid title",
            original_text="",
            idempotency_key=uuid4(),
        )


def test_create_document_chunk_accepts_valid_data():
    document_id = uuid4()

    chunk = Create_Documents_Chunks(
        document_id=document_id,
        chunk_index=0,
        content="This is a chunk.",
    )

    assert chunk.document_id == document_id
    assert chunk.chunk_index == 0
    assert chunk.content == "This is a chunk."


def test_create_document_chunk_rejects_empty_content():
    with pytest.raises(ValidationError):
        Create_Documents_Chunks(
            document_id=uuid4(),
            chunk_index=0,
            content="",
        )


def test_create_document_chunk_rejects_content_over_120_characters():
    with pytest.raises(ValidationError):
        Create_Documents_Chunks(
            document_id=uuid4(),
            chunk_index=0,
            content="a" * 121,
        )


def test_retrieve_chunk_accepts_valid_data():
    created_at = datetime.now(UTC)

    chunk = Retrieve_Chunks(
        chunk_index=2,
        content="Retrieved chunk content",
        created_at=created_at,
    )

    assert chunk.chunk_index == 2
    assert chunk.content == "Retrieved chunk content"
    assert chunk.created_at == created_at


def test_retrieve_document_accepts_valid_data():
    document_id = uuid4()
    created_at = datetime.now(UTC)
    updated_at = datetime.now(UTC)
    deleted_at = datetime.now(UTC)

    document = Retrieve_Document(
        id=document_id,
        title="Retrieved document",
        original_text="Retrieved document content",
        created_at=created_at,
        updated_at=updated_at,
        deleted_at=deleted_at,
    )

    assert document.id == document_id
    assert document.title == "Retrieved document"
    assert document.original_text == "Retrieved document content"
    assert document.created_at == created_at
    assert document.updated_at == updated_at
    assert document.deleted_at == deleted_at


def test_delete_document_command_accepts_valid_data():
    user_id = uuid4()
    document_id = uuid4()

    command = DeleteDocumentCommand(
        user_id=user_id,
        id=document_id,
    )

    assert command.user_id == user_id
    assert command.id == document_id