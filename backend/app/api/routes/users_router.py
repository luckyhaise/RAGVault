from uuid import UUID

from fastapi import APIRouter , Depends , Form , status
from app.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from app.core.exceptions.database_errors import DataError , translate_database_error, SQLAlchemyError
from app.schemas.user_schema import (ForgotPasswordChange, UserCreate, 
    UserCreateRequest , UserCreateResponse ,UserLogin ,ForgotPasswordRequest, UserCreateRequestResponse , RequestCreateAccountResponse,UserLoginResponse,ForgotPasswordRequestResponse)
from app.services.user_services import create_account_service , login_service , verify_account_service , forgot_login_password_service
user_router = APIRouter(tags=["Users"],prefix="/user")

@user_router.post(path="/request-create",response_model=RequestCreateAccountResponse,status_code=status.HTTP_201_CREATED)
async def request_create_account(user:UserCreateRequest,session:AsyncSession=Depends(get_db)):
   otp_id , task_id = await verify_account_service(session=session,user_create=user)
   return  {
       "otp_id": otp_id,
       "task_id": task_id
   } 
    

@user_router.post(path="/create",response_model=UserCreateResponse,status_code=status.HTTP_201_CREATED)
async def create_account(user:UserCreate,session:AsyncSession=Depends(get_db)):

        user_account = await create_account_service(session=session,user=user,otp=user.otp,otp_id=user.otp_id)
        return user_account

@user_router.post(path="/request-forgot-password",response_model=ForgotPasswordRequestResponse)
async def request_forgot_password(user:ForgotPasswordRequest,session:AsyncSession=Depends(get_db)):
    otp_id , task_id  = await verify_account_service(session = session , user_login= user)
    return {
        "otp_id": otp_id,
        "task_id": task_id,
    
    }

    
@user_router.post("/forgot-password")
async def forgot_password(user:ForgotPasswordChange,session:AsyncSession=Depends(get_db)):
   return await forgot_login_password_service(session=session,
        user=user,
        otp_id=user.otp_id)
  


@user_router.post(path="/login")
async def login(user:UserLogin,session:AsyncSession=Depends(get_db)):
        user_token = await login_service(session=session, user=user)
        return user_token