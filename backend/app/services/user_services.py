from sqlalchemy.ext.asyncio import AsyncSession
import logging
from app.schemas.user_schema import User_Create, User_Login
from app.core.exceptions.database_errors import run_database_operation
from app.core.security import hash_password, create_access_token , match_password
from app.repositories.users_repository import save_user , find_user_by_user_name , find_user_by_email 
from app.core.exceptions.exceptions import  UnauthorizedError

logger = logging.getLogger(__name__)


async def create_account_service(session:AsyncSession,user:User_Create):
  async def operation():
   new_user =  await save_user(session=session,
                           user_name = user.user_name,
                           phone_number= user.phone,
                           name= user.name,
                           email_id=user.email,
                           hashed_password=hash_password(user.password))
   await session.commit()
   logger.info("Account created | user_id=%s | user_name=%s", new_user.id, new_user.user_name)
   return new_user
  return await run_database_operation(session=session,operation=operation) 
    
async def login_service(session:AsyncSession,user:User_Login):
  async def operation():
    if user.user_name is not None:
     user_detail = await find_user_by_user_name(session=session,user_name=user.user_name)
    else:
     user_detail = await find_user_by_email(session=session,email=user.email)
    if user_detail is None:
      raise UnauthorizedError(internal_message=f"Account Not found. User_name:{user.user_name} User_email:{user.email} ",public_message="Invalid username/email or password")
    
    if not match_password(password=user.password, hashed_password=user_detail.password) : 
      raise UnauthorizedError(public_message="Invalid username/email or password",internal_message=f"Incorrect password input user_name: {user_detail.user_name} , password: {user.password}")
    user_id = user_detail.id
    token = create_access_token(subject=user_id)
    logger.info("Login successful | user_id=%s", user_id)
    return token
  return await run_database_operation(session=session,operation=operation)





