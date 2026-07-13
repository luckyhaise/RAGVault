from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user_schema import User_Create, User_Login
from app.core.exceptions.database_errors import run_database_operation
from app.core.security import hash_password, create_access_token
from app.repositories.users_repository import save_user , find_user_by_user_name
from app.core.exceptions.exceptions import NotFoundError

async def create_account_service(session:AsyncSession,user:User_Create):
  async def operation():
   new_user =  await save_user(session=session,
                           user_name = user.user_name,
                           phone_number= user.phone,
                           name= user.name,
                           email_id=user.email,
                           hashed_password=hash_password(user.password))
   await session.commit()
   return new_user
  return await run_database_operation(session=session,operation=operation) 
    
async def login_service(session:AsyncSession,user:User_Login):
  async def operation():
    user_detail = await find_user_by_user_name(session=session,password=user.password,user_name=user.user_name)
    if user_detail is None:
      raise NotFoundError(internal_message="Account Not found",public_message="No account exists from this user name and password")
    user_id = user_detail.id
    token = create_access_token(subject=user_id)
    return token
  return await run_database_operation(db=session,operation=operation)





