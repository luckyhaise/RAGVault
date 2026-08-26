from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from sqlalchemy import delete, select , func
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

async def view_document(user_id:UUID,session:AsyncSession,document_id:UUID,start:int,length:int):
    
    stmt = select(func.substring(Documents.original_text,start+1,length )).where(Documents.user_id== user_id,Documents.id == document_id)
    result =await session.execute(stmt)
    return  result.scalar_one()


async def get_all_user_documents(user_id:UUID,session:AsyncSession,limit:int,offset:int):
    stmt = (select(Documents).where(Documents.user_id == user_id).order_by(Documents.created_at.desc()).limit(limit).offset(offset))
    result = (await session.execute(stmt)).scalars().all()
    
    return result  

async def get_user_document_count(session:AsyncSession,user_id:UUID):
    stmt = select(func.count()).select_from(Documents).where(Documents.user_id == user_id)
    total = (await session.execute(stmt)).scalar_one()
    return total