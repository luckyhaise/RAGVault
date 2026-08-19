from enum import verify
from turtle import pu
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession
import logging

from uuid import UUID

from starlette import status
from app.models.models import Users
from app.schemas.user_schema import UserCreate, UserLogin , ForgotPasswordRequest, ForgotPasswordChange , UserCreateRequest
from app.core.exceptions.database_errors import run_database_operation
from app.core.security import hash_password, create_access_token , match_password
from app.repositories.users_repository import save_user , find_user_by_user_name , find_user_by_email 
from app.core.exceptions.exceptions import  UnauthorizedError
from app.services.helpers.otp_helper import otp_request_hanlder_for_user_service,verify_otp, EmailDeliveryError
from app.core.exceptions.exceptions import ValidationAppError



logger = logging.getLogger(__name__)

async def find_user_account_from_email_or_user_name(session:AsyncSession,user_name:str|None,email:str|None) -> Users:
    if user_name is not None:
        user_detail = await find_user_by_user_name(session=session,user_name=user_name)
    elif email is not None:
        user_detail = await find_user_by_email(session=session,email=email)
    else: 
        raise ValidationAppError(public_message="Please enter email or user name")
    if user_detail is None:
        raise UnauthorizedError(internal_message=f"Account Not found. User_name:{user_name} User_email:{email} ",
            public_message="Invalid username/email or password")
    return user_detail 
    


async def verify_account_service(session:AsyncSession,user_create:UserCreateRequest|None=None,user_login:ForgotPasswordRequest|None=None):
    """""This service can be used to verify account. This generates a otp and sends it to user's email. 
         It returns a celery task id of email request and OTP id"""
    
    user = user_login if user_login is not None else user_create
    if user is None:
        raise ValidationAppError(public_message="Please enter username or email")
    purpose = "login" if user_login else "create_account"
    if purpose == "login":
      user_detail =await  find_user_account_from_email_or_user_name(email=user.email,user_name=user.user_name,session=session)
      email = user_detail.email
    else :
        email = user.email
    otp_id,task_id =await otp_request_hanlder_for_user_service(session=session,purpose=purpose,email=str(email))
    return otp_id, task_id 
  
async def forgot_login_password_service(session:AsyncSession,user:ForgotPasswordChange,otp_id:UUID):
    allowed = await verify_otp(otp=user.otp,otp_id=otp_id,purpose="login",session=session,email=str(user.email))
    async def operation():
        user_detail = await find_user_account_from_email_or_user_name(email=user.email,user_name=user.user_name, session=session)
        user_detail.password = hash_password(user.new_password)
        await session.commit()
        return {"message": "Password changed successfully."}
    if allowed is True:
        return await run_database_operation(operation=operation,session=session)
    else:
        raise EmailDeliveryError(
                           public_message="Incorrect OTP. Please try again",
                           error_code="UNAUTHORIZED",
                           status_code=401
                       )
        
    

async def create_account_service(session:AsyncSession,user:UserCreate,otp:str,otp_id:UUID):
  allowed =await verify_otp(otp=otp,otp_id=otp_id,purpose="create_account",session=session,email=user.email)
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
  if allowed is True :
      return await run_database_operation(session=session,operation=operation) 
  else :
      
      raise EmailDeliveryError(
                         public_message="Incorrect OTP. Please try again",
                         error_code="UNAUTHORIZED",
                         status_code=401
                     )
async def login_service(session:AsyncSession,user:UserLogin):
  async def operation():
    if user.user_name is not None:
     user_detail = await find_user_by_user_name(session=session,user_name=user.user_name)
    else:
     user_detail = await find_user_by_email(session=session,email=str(user.email))
    if user_detail is None:
      raise UnauthorizedError(internal_message=f"Account Not found. User_name:{user.user_name} User_email:{user.email} ",public_message="Invalid username/email or password")
    
    if not match_password(password=user.password, hashed_password=user_detail.password) : 
      raise UnauthorizedError(public_message="Invalid username/email or password",internal_message=f"Incorrect password input user_name: {user_detail.user_name} , password: {user.password}")
    user_id = user_detail.id
    token = create_access_token(subject=str(user_id))
    logger.info("Login successful | user_id=%s", user_id)
    return {"access_token":token}
  return await run_database_operation(session=session,operation=operation)





