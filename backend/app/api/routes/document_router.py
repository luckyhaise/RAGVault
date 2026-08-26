from fastapi import APIRouter , Depends , Form  
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession  

from app.services.document.document_presistence_service import save_document_service
from app.schemas.ingestion_jobs_schema import IngestionJobsResponse
from app.schemas.documents_schema import CreateDocumentsCommand , DeleteDocumentCommand


from app.db.database import get_db 
from app.api.dependencies.upload_file_validation import validate_file
from app.api.dependencies.validate_token import validate_token_and_get_user_id
document_router = APIRouter(tags=["document"],prefix="/document")
@document_router.post(path="/document/upload",response_model=IngestionJobsResponse)
async def save_document(user_id:UUID= Depends(validate_token_and_get_user_id),session:AsyncSession =Depends(get_db),validated_document:tuple[str,str]= Depends(validate_file) ,idempotency_key:UUID = Form(...)):
    original_file , title = validated_document
    
    command = CreateDocumentsCommand(user_id=user_id,title=title,original_text=original_file,idempotency_key=idempotency_key)

    return  await save_document_service(session=session,command=command)
    
    
async def delete_document(document_id:UUID=Form(...),user_id:UUID = Depends(validate_token_and_get_user_id),session:AsyncSession = Depends(get_db)):
    command = DeleteDocumentCommand(user_id=user_id,document_id=document_id)
    
 