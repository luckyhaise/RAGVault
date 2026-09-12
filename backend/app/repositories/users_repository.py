# from app.schemas.user_schema import User_Create,User_Login
from datetime import datetime
from uuid import UUID

from sqlalchemy import select , update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from app.models.models import Users, UserSession

async def change_user_details_with_user_id(
    session: AsyncSession, 
    user_id: UUID, 
    detail: InstrumentedAttribute,  
    new_value: str|UUID
):
   
    query = update(Users).where(Users.id == user_id).values({detail: new_value}).returning(detail)
    result =  (await session.execute(query)).scalar_one()
    await session.flush()
    return result




async def find_user_by_user_id(user_id:UUID,session:AsyncSession):
    stmt = select(Users).where(Users.id ==user_id)
    return (await session.execute(stmt)).scalar_one_or_none()

async def save_user(name:str,email_id:str,hashed_password:str,user_name:str,session:AsyncSession):
    user = Users(user_name = user_name, name = name,email = email_id , password = hashed_password)
    session.add(user)
    await session.flush()
    return user
async def find_user_by_user_name(session:AsyncSession,user_name:str):
    
    user = select(Users).where(Users.user_name== user_name) 
    user =  (await session.execute(user)).scalar_one_or_none()
    return user

async def find_user_by_email(session:AsyncSession,email:str) :
    user = select(Users).where(Users.email == email )
    user = (await session.execute(user)).scalar_one_or_none()
    return user

async def reset_password(session:AsyncSession,user_id:UUID):
    user = select(Users).where(Users.id == user_id).with_for_update()
    user = (await session.execute(user)).scalar_one_or_none()
    return user 

async def create_session(session:AsyncSession,user_id:UUID,is_revoked:bool,refresh_token_jti:UUID,expires_at:datetime):
    stmt = UserSession(user_id=user_id,refresh_token_jti=refresh_token_jti,is_revoked=is_revoked,expires_at=expires_at)
    session.add(stmt)
    await session.flush()
    return stmt 

    
async def find_user_session_by_user_id_for_update(session:AsyncSession,user_id:UUID,refresh_token_jti:UUID):
    stmt = select(UserSession).where(UserSession.user_id == user_id,UserSession.refresh_token_jti==refresh_token_jti).with_for_update()
    user_session = (await session.execute(stmt)).scalar_one_or_none()
    
    return user_session