from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.validate_token import (
   validate_token_and_get_user_id,
   validate_token_for_refresh,
)
from app.db.database import get_db
from app.schemas.user_schema import (
   CreateAccountRequestResponse,
   ForgotPasswordChange,
   ForgotPasswordRequest,
   ForgotPasswordRequestResponse,
   LoginResponse,
   RefreshTokenResponse,
   ResetPassword,
   UserCreate,
   UserCreateRequest,
   UserCreateResponse,
   UserLogin,
   UserProfileResponse,
   ChangeUserDetail
)
from app.services.user import (
   change_password_service,
   create_account_service,
   forgot_login_password_service,
   get_user_profile_service,
   login_service,
   logout_service,
   refresh_token_service,
   verify_account_service,
   change_user_detail_service
)

user_router = APIRouter(tags=["Users"],prefix="/user")

@user_router.post(path="/request-create",response_model=CreateAccountRequestResponse,status_code=status.HTTP_201_CREATED)
async def request_create_account_route(user:UserCreateRequest,session:AsyncSession=Depends(get_db)):
   """It is required the special characters and rules to be made explicit to the user creating the account"""
   """-Password must have atleast one uppercase character.
      -Password must have atleast one lowercase character.
      -Password must have atleast one digit.
      -Password must have atleast one special character @ # _ ! $ % * . - 
      """
   otp_id , task_id = await verify_account_service(session=session,user_create=user)
   return  {
       "otp_id": otp_id,
       "task_id": task_id
   } 
    

@user_router.post(path="/create",response_model=UserCreateResponse,status_code=status.HTTP_201_CREATED)
async def create_account_route(user:UserCreate,session:AsyncSession=Depends(get_db)):

        user_account = await create_account_service(session=session,user=user,otp=user.otp,otp_id=user.otp_id)
        return user_account

@user_router.post(path="/request-forgot-password",response_model=ForgotPasswordRequestResponse)
async def request_forgot_password_route(user:ForgotPasswordRequest,session:AsyncSession=Depends(get_db)):
    otp_id , task_id  = await verify_account_service(session = session , user_login= user)
    return {
        "otp_id": otp_id,
        "task_id": task_id,
    
    }

    
@user_router.post("/forgot-password")
async def forgot_password_route(user:ForgotPasswordChange,session:AsyncSession=Depends(get_db))-> dict[str,str]:
   return await forgot_login_password_service(session=session,
        user=user,
        otp_id=user.otp_id)
  


@user_router.post(path="/login",response_model=LoginResponse)
async def login_route(user:UserLogin,session:AsyncSession=Depends(get_db)):
        user_token = await login_service(session=session, user=user)
        return user_token

@user_router.post(path="/refresh-token",response_model=None)
async def refresh_token_route(refresh_token:str=Depends(validate_token_for_refresh),session:AsyncSession=Depends(get_db)):
   token =await refresh_token_service(refresh_token=refresh_token,session=session)
   return token

@user_router.post(path="/logout",response_model=RefreshTokenResponse)
async def logout_user_route(session:AsyncSession= Depends(get_db),refresh_token:str=Depends(validate_token_for_refresh)):
     return await logout_service(refresh_token=refresh_token,session=session)

@user_router.post(path="/change-password",response_model=None)
async def change_password_route(user:ResetPassword,session:AsyncSession=Depends(get_db),user_id:UUID=Depends(validate_token_and_get_user_id)):
     return await change_password_service(session=session,user=user,user_id=user_id)

@user_router.post(path="/change-user-detail")
async def change_user_detail_route(user_detail:ChangeUserDetail,session:AsyncSession=Depends(get_db),user_id:UUID=Depends(validate_token_and_get_user_id)):
    return await change_user_detail_service(field=user_detail.field,new_value=user_detail.new_value,user_id=user_id,session=session,password=user_detail.password)

@user_router.get(path="/me",response_model=UserProfileResponse)
async def get_user_profile_route(session:AsyncSession=Depends(get_db),user_id:UUID=Depends(validate_token_and_get_user_id)):
   """Return the account details of the user identified by the access token."""
   return await get_user_profile_service(session=session,user_id=user_id)