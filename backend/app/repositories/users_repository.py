# from app.schemas.user_schema import User_Create,User_Login
from app.models.models import Users
from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy import select

async def save_user(phone_number:int,name:str,email_id:str,hashed_password:str,user_name:str,session:AsyncSession):
    user = Users(user_name = user_name,phone = phone_number , name = name,email = email_id , password = hashed_password)
    session.add(user)
    await session.flush()
    return user

async def find_user_by_user_name(session:AsyncSession,password:str,user_name:str):

    user = select(Users).where(Users.user_name== user_name,Users.password==password) 
    user =  (await session.execute(user)).scalar_one_or_none()
    return user

async def find_user_by_email(session:AsyncSession,password:str,email:str):
    user = select(Users).where(Users.email == email , Users.password == password)
    user = (await session.execute(user)).scalar_one_or_none()
    return user

async def reset_password(session:AsyncSession,password:str,new_password:str,email:str):
    user = select(Users).where(Users.email == email,Users.password == password)
    user = (await session.execute(user)).scalar_one_or_none()
    if user:
        user.password = new_password 
        await session.flush()
        return user
    return None

