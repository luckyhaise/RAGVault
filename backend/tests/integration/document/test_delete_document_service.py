import random
import string
from unittest.mock import patch
from uuid import uuid4

import pytest
from account_helper import ensure_user
from sqlalchemy.exc import IntegrityError

from app.core.exceptions.exceptions import DataBaseError
from app.models.models import Documents
from app.services.document_service import (
    CreateDocumentsCommand,
    DeleteDocumentCommand,
    delete_document_service,
    save_document_service,
)

document = "".join(random.choices(string.ascii_letters + string.digits,k=1000))

def create_integrity_error(constraint_name):
    class FakeDiag:
        def __init__(self,constraint_name):
            self.constraint_name = constraint_name
    
    return IntegrityError(statement="INSERT INTO users (email) VALUES (:email)",
        params={"email": "test@example.com"},
        orig=FakeDiag(constraint_name),
    )


@pytest.mark.asyncio
async def test_delete_document(db_session):
    user = await ensure_user(db_session=db_session)
    idempotency_key = uuid4()
    saved_job =  await save_document_service(session=db_session,command=CreateDocumentsCommand(
        user_id=user.id,
        title = "Test Document",
        original_text=document,
        idempotency_key=idempotency_key
    ))
    document_id = saved_job.get("document_id")
    retrieved_document =await db_session.get(Documents,document_id)
    assert retrieved_document is not None
    result = await delete_document_service(session=db_session,command=DeleteDocumentCommand(
        user_id=user.id,
        id = document_id
    ))
    
    retrieved_document =await db_session.get(Documents,document_id)
    assert retrieved_document is None
    assert result.rowcount >0
@pytest.mark.asyncio
async def test_delete_document_fails(db_session):
    user = await ensure_user(db_session=db_session)
    with patch("app.services.document_service.delete_document",
    side_effect=create_integrity_error("uq_email"),):
        with pytest.raises(DataBaseError) as excinfo:
                await delete_document_service(session=db_session,command=DeleteDocumentCommand(
                     user_id=user.id,
                     id = uuid4()
                 ))
    assert  "INSERT INTO users (email) VALUES (:email)" in excinfo.value.internal_message

    assert excinfo.value.error_code == "EMAIL_ALREADY_EXISTS"

@pytest.mark.asyncio
async def test_delete_document_does_not_delete_another_users_document(
    db_session,
):
    owner = await ensure_user(db_session=db_session)
    other_user = await ensure_user(db_session=db_session,i=2)
    idempotency_key = uuid4()

    saved_job = await save_document_service(
        session=db_session,
        command=CreateDocumentsCommand(
            user_id=owner.id,
            title="Test Document",
            original_text=document,
            idempotency_key=idempotency_key,
        ),
    )

    document_id = saved_job.get("document_id")

    result = await delete_document_service(
        session=db_session,
        command=DeleteDocumentCommand(
            user_id=other_user.id,
            id=document_id,
        ),
    )

    assert result.rowcount == 0

    retrieved_document = await db_session.get(
        Documents,
        document_id,
    )

    assert retrieved_document is not None
    assert retrieved_document.user_id == owner.id
    
    
