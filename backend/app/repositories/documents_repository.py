from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from sqlalchemy import delete
from app.models.models import Documents
async def create_document(user_id:UUID,session:AsyncSession,title:str,original_text:str):
    document  = Documents(user_id=user_id,title = title,original_text = original_text)
    session.add(document)
    await session.flush()
    return document
async def delete_document(user_id:UUID,session:AsyncSession,document_id:UUID):
    stmt = delete(Documents).where(Documents.id == document_id,Documents.user_id == user_id)
    result = await session.execute(stmt)
    return result
    
    
