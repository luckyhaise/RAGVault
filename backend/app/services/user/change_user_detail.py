from typing import Literal
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions.database_errors import translate_database_error
from app.core.exceptions.exceptions import AppError, UnauthorizedError
from app.core.security import match_password
from app.infrastructure.redis.rate_limit import (
    redis_check_user_rate_limit,
    redis_get_attempts_left,
)
from app.models.models import Users
from app.repositories.users_repository import (
    change_user_details_with_user_id,
    find_user_by_user_id,
)


async def change_user_detail_service(session:AsyncSession,user_id:UUID,field :Literal["user_name","email","name"],new_value:UUID|str,password:str):
   try: 
     limit = settings.log_in_attempts
     key = f"user:change_user_detail{field}"
     allowed = redis_check_user_rate_limit(limit=settings.log_in_attempts,window=settings.log_in_block_window_sec,key=key) 
     if not allowed:
          raise UnauthorizedError(public_message=f"Your {field} change limit has exhausted, Please try again after {int(settings.log_in_block_window_sec)/60} minutes. ")
        
     user_detail = await  find_user_by_user_id(session=session,user_id=user_id)
    
     if not match_password(password,user_detail.password) :
        attempts_left = await redis_get_attempts_left(key=key,limit=limit)
        raise UnauthorizedError(public_message=f"Password you entred is incorrect, {attempts_left} are left")
    

     result =  await change_user_details_with_user_id(user_id=user_id,session=session,detail=getattr(Users,field),new_value=new_value) 

     await session.commit()
     return {"detail":f"Your {field} has been changed to {result}"} 
   

   except SQLAlchemyError as exc :
     await session.rollback()
     raise translate_database_error(exc=exc) from exc
   except Exception as exc:
       raise AppError(error_code="UNEXPECTED_ERROR",internal_message=(str),public_message="Unexpected Error occured, Please try again later",status_code=500) from exc 
     
