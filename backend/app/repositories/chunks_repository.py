from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.models import Documents_Chunks
async def save_chunks(document_id:UUID,chunks:list[str],session:AsyncSession):
    
    document_chunks = [Documents_Chunks(document_id=document_id,chunk_index=i,content = chunk) for i,chunk in enumerate(chunks)]
    session.add_all(document_chunks)
    await session.flush()
    return document_chunks

