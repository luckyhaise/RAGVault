from pydantic import BaseModel , Field 
from typing import Literal
from uuid import UUID
from datetime import datetime
class Create_Ingestion_Jobs(BaseModel):
    user_id: UUID = Field(description="The unique identifier of the user who owns this Job")
    document_id : UUID = Field(description="The unique identifier of the document for this Job")

class Ingestion_Jobs_Response(BaseModel):
    id:UUID = Field(description="Unique indetifier of the jobs")
    status:Literal["pending","completed","failed","processing"] = Field(description="Status of the Job")
    error_message:str| None = Field(description="Error message if any", default= None)
    idempotency_key: str = Field(description="Idempotancy key of the job")
    completed_at:datetime = Field("Time when job was completed")

    updated_at:datetime = Field("Time when document was last updated")
    created_at : datetime = Field("Time when document was created")
