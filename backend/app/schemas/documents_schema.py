from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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
    page:int = Field(...,ge=1,description="Page number")

class RetrieveDocument(BaseModel):
    id: UUID = Field(description="Unique identifier of the document")
    start : int = Field(description="Starting index of the document i.e offset of character position",ge=0)
    limit:int = Field(..., le=100000,ge=1,description="Number of characters in a page")
    prev:bool = Field(default=False,description="Load previous data")

class DeleteDocumentCommand(BaseModel):
    user_id: UUID
    id:UUID

class DocumentSummary(BaseModel):
    """A page item returned by the document list endpoint."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID = Field(description="Unique identifier of the document")
    title: str = Field(description="Title of the document")
    created_at: datetime = Field(description="Time when the document was created")
    updated_at: datetime = Field(description="Time when the document was last updated")

class DocumentListPagination(BaseModel):
    total_items: int = Field(description="Total number of documents the user owns")
    total_pages: int = Field(description="Total number of pages available")
    has_next: bool = Field(description="Whether a next page exists")
    has_previous: bool = Field(description="Whether a previous page exists")

class RetrieveAllUserDocumentsResponse(BaseModel):
    items: list[DocumentSummary] = Field(description="Documents for the requested page")
    pagination: DocumentListPagination = Field(description="Pagination metadata")
