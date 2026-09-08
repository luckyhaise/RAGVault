import random
import string
from unittest.mock import patch
from uuid import uuid4

import pytest
from account_helper import ensure_user

from app.core.exceptions.exceptions import AppError, DataBaseError
from app.models.models import Documents
from app.repositories.ingestion_job_repository import get_by_idempotency_key
from app.services.document_service import CreateDocumentsCommand, save_document_service
from app.utils.chunk_data import chuckey_chunkey

document = "".join(random.choices(string.ascii_letters + string.digits,k=1000))

@pytest.mark.asyncio 
async def test_save_document_service_saves_document_and_idempotancy_key_works(db_session):
    user =  await ensure_user(db_session=db_session)
    idempotency_key = uuid4()



    saved_document = await save_document_service(session=db_session,
                                                 command=CreateDocumentsCommand(user_id=user.id , 
                                                                                title="test document",
                                                                                original_text=document,
                                                                                idempotency_key=idempotency_key))

    print(saved_document)
    assert saved_document.get("user_id")== user.id
    assert saved_document.get("created_at") is not None
    assert saved_document.get("status") == "completed"
    assert saved_document.get("id" ) is not None
    assert saved_document.get("idempotency_key") == idempotency_key
    saved_document2 = await save_document_service(session=db_session,
                                                  command=CreateDocumentsCommand(user_id=user.id , 
                                                                                 title="test document2",
                                                                                 original_text=document,
                                                                                 idempotency_key=idempotency_key))
    assert saved_document.get("id") == saved_document2.get("id")

@pytest.mark.asyncio
async def test_save_document_saves_preserves_chunks_and_document(db_session):
    user =  await ensure_user(db_session=db_session)
    idempotency_key = uuid4()


    saved_job = await save_document_service(session=db_session,
                                                 command=CreateDocumentsCommand(user_id=user.id , 
                                                                                title="test document",
                                                                                original_text=document,
                                                                                idempotency_key=idempotency_key))

    document_retrieved:Documents= await db_session.get(Documents,saved_job.get("document_id"))
    assert document_retrieved.original_text == document
    # refresh to load the chunks in orm
    await db_session.refresh(
    document_retrieved,
    attribute_names=["chunks"]
     )
    chunks = chuckey_chunkey(doc=document)
    retrieved_chunks = [chunk.content  for chunk in document_retrieved.chunks ]
    for chunk_content,chunk in zip(retrieved_chunks,chunks):
        assert chunk_content == chunk


@pytest.mark.asyncio
# @patch("app.services.document_service.create_document")
@patch("app.services.document_service.start_ingestion_job") 
async def test_start_ingestion_job_fails(mock_start_ingestion_job,db_session):
    user = await ensure_user(db_session=db_session)
    
    error = DataBaseError(public_message="Something went wrong. Please try again later",
                         internal_message= "Some internal error",
                         error_code="SQL_ALCHEMY_ERROR",
                         status_code=500)
    mock_start_ingestion_job.side_effect = error
    with patch("app.services.document_service.create_document") as  mock_create_document:
      
   
     with pytest.raises(AppError) as excinfo:
        idempotency_key = uuid4()
        await save_document_service(session=db_session,
                                    command=CreateDocumentsCommand(
                                        user_id= user.id,
                                        title="Test Document"
                                         ,
                                         original_text= document,
                                         idempotency_key= idempotency_key
                                    )


        )
        mock_create_document.assert_not_awaited()
   

    assert excinfo.value.error_code == "SQL_ALCHEMY_ERROR"
    mock_start_ingestion_job.assert_awaited_once()

@pytest.mark.asyncio 
async def test_save_chunks_failed_and_ingestion_job_marked(db_session):
    idempotency_key = uuid4()
    user = await ensure_user(db_session=db_session)
    user_id = user.id 
    error = DataBaseError(public_message="failed to save chunks",error_code="CHUNK_SAVE_FAILED",internal_message="chunk save failed")
    with patch("app.services.document_service.save_chunks",side_effect=error) as mock_save_chunk:
        with pytest.raises(AppError) as excinfo:
              await save_document_service(session=db_session,
                                                command=CreateDocumentsCommand(
                                                    user_id= user.id,
                                                    title="Test Document"
                                                     ,
                                                     original_text= document,
                                                     idempotency_key= idempotency_key
                                                )

                )
        assert excinfo.value.error_code == "CHUNK_SAVE_FAILED"
        assert excinfo.value.public_message == "failed to save chunks"
        assert excinfo.value.internal_message == "chunk save failed"
        mock_save_chunk.assert_awaited_once()
    saved_job = await get_by_idempotency_key(session=db_session,user_id = user_id,idempotency_key=idempotency_key)
    assert saved_job.status == "failed"
    assert saved_job.error_message == "chunk save failed"