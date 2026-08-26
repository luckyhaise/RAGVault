from pydantic import BaseModel, Field , ConfigDict
from uuid import UUID
from datetime import datetime 


class CreateDocumentsCommand(BaseModel):
    user_id : UUID = Field(description="The unique identifier of the user who owns this document")
    title : str = Field(min_length=1,max_length=200, description="Title of the document")
    original_text: str =  Field(min_length=1,max_length=500_000, description="The content of the document")
    idempotency_key: UUID = Field(description="Idempotancy key of the job")

class Create_Documents_Chunks(BaseModel):
    document_id : UUID =Field(description="The unique identifier of the document which is cuncked")
    chunk_index : int = Field(description="Index Number of the specific chunk")
    content: str = Field(max_length=120,min_length=1,description="Content of the chunks document is divided into")

class RetrieveAllUserDocuments(BaseModel):
    user_id:UUID 
    limit:int = Field(..., le=100,ge=1,description="Number of rows in a page")
    page:int = Field(...,le=1,description="Page number")

class RetrieveDocument(BaseModel):
    

class Retrieve_Document(BaseModel):
    id: UUID = Field(description="Unique identifier of the document")
    title: str = Field(description="Title of the document")
    original_text: str = Field(description="The content of the document")
    created_at:datetime = Field(description="The time when document was created")
    updated_at:datetime = Field(description= "The time when document was last updated")
    deleted_at:datetime|None = Field(description="Date and time of document being deleted at",default= None)

class DeleteDocumentCommand(BaseModel):
    user_id : UUID = Field(description="The unique identifier of the user who owns this document")
    id: UUID = Field(description="Unique identifier of the document")

