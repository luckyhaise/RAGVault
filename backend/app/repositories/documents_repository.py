from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Documents


async def create_document(user_id:UUID,session:AsyncSession,title:str,original_text:str)->Documents:
    document  = Documents(user_id=user_id,title = title,original_text = original_text)
    session.add(document)
    await session.flush()
    return document
async def delete_document(user_id:UUID,session:AsyncSession,document_id:UUID):
    stmt = select(Documents).where(Documents.id == document_id,Documents.user_id == user_id)
    result = (await session.execute(stmt)).scalar_one()
    
    title = result.title
    await session.delete(result)
    
    return title

async def view_document(user_id:UUID,session:AsyncSession,document_id:UUID,start:int,limit:int,prev:bool=False)->str:
    if prev:
        calculated_start = max(0,start-limit)
        calculated_length = start - calculated_start
        stmt = select(func.substring(Documents.original_text,calculated_start+1,calculated_length)).where(Documents.user_id== user_id,Documents.id == document_id)
    else:
        stmt = (
                    select(func.substring(Documents.original_text, start + 1, limit))
                    .where(Documents.user_id == user_id, Documents.id == document_id)
                )


    result =await session.execute(stmt)
    return   result.scalar_one()
async def user_document_size(user_id:UUID,session:AsyncSession,document_id:UUID)-> int :
    stmt = select(func.char_length(Documents.original_text)).where(Documents.user_id== user_id,Documents.id == document_id )
    result = await session.execute(stmt)
    return result.scalar_one()

async def get_all_user_documents(user_id:UUID,session:AsyncSession,limit:int,offset:int)-> Sequence[Documents]:
    stmt = (select(Documents.id,Documents.created_at,Documents.title,Documents.updated_at,Documents).where(Documents.user_id == user_id).order_by(Documents.created_at.desc()).limit(limit).offset(offset))
    result = (await session.execute(stmt)).scalars().all()

    return result

async def get_user_document_count(session:AsyncSession,user_id:UUID) -> int:
    stmt = select(func.count()).select_from(Documents).where(Documents.user_id == user_id)
    total = (await session.execute(stmt)).scalar_one()
    return total
