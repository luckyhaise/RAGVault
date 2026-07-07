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

class Retrieve_Chunks(BaseModel):
     model_config = ConfigDict(from_attributes=True)
     chunk_index: int = Field(description="Index of the chunks")
     content : str = Field(description="The content of each individual chunk")
     created_at : datetime = Field(description="Time when the chunk was created")

class Retrieve_Document(BaseModel):
    id: UUID = Field(description="Unique identifier of the document")
    title: str = Field(description="Title of the document")
    original_text: str = Field(description="The content of the document")
    created_at:datetime = Field(description="The time when document was created")
    updated_at:datetime = Field(description= "The time when document was last updated")
    deleted_at:datetime = Field(description="Date and time of document being deleted at")

