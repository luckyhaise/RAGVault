from uuid import UUID

from pydantic import BaseModel, Field


class CreateDocumentsCommand(BaseModel):
    user_id : UUID = Field(description="The unique identifier of the user who owns this document")
    title : str = Field(min_length=1,max_length=200, description="Title of the document")
    original_text: str =  Field(min_length=1,max_length=500_000, description="The content of the document")
    idempotency_key: UUID = Field(description="Idempotancy key of the job")

class CreateDocumentsChunks(BaseModel):
    document_id : UUID =Field(description="The unique identifier of the document which is cuncked")
    chunk_index : int = Field(description="Index Number of the specific chunk")
    content: str = Field(max_length=120,min_length=1,description="Content of the chunks document is divided into")

class RetrieveAllUserDocuments(BaseModel):
    limit:int = Field(..., le=100,ge=1,description="Number of rows in a page")
    page:int = Field(...,le=1,description="Page number")

class RetrieveDocument(BaseModel):
    id: UUID = Field(description="Unique identifier of the document")
    start : int = Field(description="Starting index of the document i.e offset of character position",ge=0)
    limit:int = Field(..., le=100000,ge=1,description="Number of characters in a page")
    prev:bool = Field(default=False,description="Load previous data")

class DeleteDocumentCommand(BaseModel):
    user_id: UUID
    id:UUID
