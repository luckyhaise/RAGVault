import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID
from typing import Literal

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Users
from app.services.helpers.helper_services import find_user_account_from_email_or_user_name
from app.core.config import settings
from app.core.exceptions.database_errors import translate_database_error
from app.core.exceptions.exceptions import (
    AppError,
    
    NotFoundError,
    UnauthorizedError,
    ValidationAppError,
    ConflictError
)
from app.core.security import create_token, decode_token, hash_password, match_password
from app.infrastructure.redis.rate_limit import redis_check_user_rate_limit, redis_get_attempts_left
from app.repositories.users_repository import (
    create_session,
    find_user_by_email,
    find_user_by_user_id,
    find_user_by_user_name,
    find_user_session_by_user_id_for_update,
    reset_password,
    save_user,
    change_user_details_with_user_id
)
from app.schemas.user_schema import (
    ForgotPasswordChange,
    ResetPassword,
    UserCreate,
    UserLogin,
    UserCreateRequest,
    ForgotPasswordRequest
)
from app.services.helpers.otp_helper import (
    EmailDeliveryError,
    verify_otp,
    otp_request_hanlder_for_user_service
)



logger = logging.getLogger(__name__)


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
    if allowed is not True:
        raise EmailDeliveryError(
                           public_message="Incorrect OTP. Please try again",
                           error_code="UNAUTHORIZED",
                           status_code=401
                       )
    try:
        user_detail = await find_user_account_from_email_or_user_name(email=user.email,user_name=user.user_name, session=session)
        if match_password(user.new_password,user_detail.password):
            ConflictError(public_message="Please enter a new password not similar to the old ones")
        user_detail.password = hash_password(user.new_password)
        await session.commit()
        return {"message": "Password changed successfully."}
    except SQLAlchemyError as exc:
        await session.rollback()
        raise translate_database_error(exc=exc) from exc



async def create_account_service(session:AsyncSession,user:UserCreate,otp:str,otp_id:UUID):
  allowed =await verify_otp(otp=otp,otp_id=otp_id,purpose="create_account",session=session,email=user.email)
  if allowed is not True:
      raise EmailDeliveryError(
                         public_message="Incorrect OTP. Please try again",
                         error_code="UNAUTHORIZED",
                         status_code=401
                     )
  try:
        new_user =  await save_user(session=session,
                            user_name = user.user_name,
                            name= user.name,
                            email_id=user.email,
                            hashed_password=hash_password(user.password))
        await session.commit()
        logger.info("Account created | user_id=%s | user_name=%s", new_user.id, new_user.user_name)
        return new_user
  except SQLAlchemyError as exc:
        await session.rollback()
        raise translate_database_error(exc=exc) from exc
async def login_service(session:AsyncSession,user:UserLogin):
  try:
    if user.user_name is not None:
     user_detail = await find_user_by_user_name(session=session,user_name=user.user_name)
    else:
     user_detail = await find_user_by_email(session=session,email=str(user.email))
    if user_detail is None:
      raise UnauthorizedError(internal_message=f"Account Not found. User_name:{user.user_name} User_email:{user.email} ",public_message="Invalid username/email or password")

    if not match_password(password=user.password, hashed_password=user_detail.password) :
      raise UnauthorizedError(public_message="Invalid username/email or password",internal_message=f"Incorrect password input user_name: {user_detail.user_name}")
    user_id = user_detail.id
    token = create_token(subject=str(user_id),create_refresh_token=True)
    logger.info("Login successful | user_id=%s", user_id)
    

    user_session =  await create_session(session=session,
        expires_at=token.refresh_expires_at,
        is_revoked=False,
        refresh_token_jti=token.refresh_jti,
        user_id=user_id)
    await session.commit()

    logger.info("Session Created | session_id=%s", user_session.id)
    return {"access_token":token.access_token,
           "refresh_token":token.refresh_token}
  except SQLAlchemyError as exc:
    await session.rollback()
    raise translate_database_error(exc=exc) from exc

@dataclass
class Token:
    access_token:str
    refresh_token:str|None

async def refresh_token_service(session:AsyncSession,refresh_token:str):
    try:
        decoded= decode_token(expected_type="refresh",token=refresh_token)
        now = datetime.now(UTC)


        refresh_renew_threshold = timedelta(days=settings.refresh_token_expire_days *  .25)
        user_id = UUID(decoded["sub"])
        async with session.begin():
                user_session = await find_user_session_by_user_id_for_update(session=session,user_id=user_id,refresh_token_jti=UUID(decoded["jti"]))


                if user_session is None:
                    raise UnauthorizedError(
                        internal_message=f"No session is found from the user_id={user_id} | refresh_token_jti={decoded['jti']}",
                        public_message="Your session is invalid please login again",
                    )
                if  str(user_session.refresh_token_jti) != str(decoded["jti"])  :
                        print(f"{decoded["jti"]} and {user_session.refresh_token_jti}")
                        raise UnauthorizedError(
                            internal_message=(
                                f"The refresh_token_jti does not match session_jti | "
                                f"session_user_id={user_session.user_id} | "
                                f"session_jti={user_session.refresh_token_jti} | "
                                f"refresh_token_jti={decoded['jti']}"
                            ),
                            public_message="Your session is invalid. Please login again.",
                        )

                if user_session.expires_at < now:
                    raise UnauthorizedError(internal_message=f"Refresh token for user_id: {user_id} has expired",
                        public_message="Your session has expired please login again")
                if user_session.is_revoked is True:
                    raise UnauthorizedError(internal_message=f"Refresh token for user_id: {user_id} has is revoked",
                        public_message="Your session has been revoked please login again")
                should_rotate_refresh_token = (
                        user_session.expires_at - now < refresh_renew_threshold
                    )

                token = create_token(subject=str(user_id),create_refresh_token=should_rotate_refresh_token)
                if should_rotate_refresh_token:
                    user_session.expires_at = token.refresh_expires_at
                    user_session.refresh_token_jti = token.refresh_jti
                    return Token(access_token=token.access_token,refresh_token=token.refresh_token)

                return Token(access_token=token.access_token,refresh_token=None)

    except (UnauthorizedError,AppError):
        raise
    except SQLAlchemyError as exc:
       raise translate_database_error(exc=exc) from exc
    except Exception as exc:
        raise AppError(error_code="UNEXPECTED_ERROR",status_code=500,internal_message=str(exc),public_message="An unexpected error has occured. Please login again") from exc



async def logout_service(session:AsyncSession,refresh_token:str):
    try:
        now = datetime.now(UTC)
        decoded= decode_token(token=refresh_token,expected_type="refresh")
        user_id = decoded["sub"]
        async with session.begin():
            user_session =await find_user_session_by_user_id_for_update(session=session,user_id=user_id,refresh_token_jti=UUID(decoded["jti"]))
            if user_session is None :
                raise UnauthorizedError(
                    internal_message=f"No user session exists for the refresh token with user id={user_id}",
                    public_message="Invalid session. Please login again",
                )
            if user_session.refresh_token_jti != decoded["jti"]:
                raise UnauthorizedError(
                    internal_message=(
                        f"The refresh_token_jti does not match session_jti | "
                        f"session_user_id={user_session.user_id} | "
                        f"session_jti={user_session.refresh_token_jti} | "
                        f"refresh_token_jti={decoded['jti']}"
                    ),
                    public_message="Your session is invalid. Please login again.",
                )
            if user_session.expires_at < now:
                    raise UnauthorizedError(internal_message=f"Refresh token for user_id: {user_id} has expired",
                        public_message="Your session has expired please login again")
            if user_session.is_revoked:
                raise UnauthorizedError(
                    internal_message=f"Duplicate logout request for an already revoked account by user_id={user_id}",
                    public_message="Your account has already been logged out. Please login again",
                )
            else :
                user_session.is_revoked = True
                return {"detail":f"Logout request sucessful {user_id}"}
    except (UnauthorizedError,AppError):
        raise
    except SQLAlchemyError as exc:
       raise translate_database_error(exc=exc) from exc
    except Exception as exc:
        raise AppError(error_code="UNEXPECTED_ERROR",status_code=500,internal_message=str(exc),public_message="An unexpected error has occured. Please login again") from exc

async def change_password_service(session:AsyncSession,user_id:UUID,user:ResetPassword):
    try:
            allowed = redis_check_user_rate_limit(key=f"password:change_password:{user_id}",limit=settings.log_in_attempts,window=settings.log_in_block_window_sec)
            if not allowed:
                raise UnauthorizedError(public_message=f"Password attempts limit reached. Please try again after {round(settings.log_in_block_window_sec/60)} minutes")
            async with session.begin():
                result =  await reset_password(session=session,user_id=user_id)
                if result is None:
                    raise UnauthorizedError(public_message="Invalid session.Please login again",internal_message=f"No user account has been found for change password request by user_id: {user_id}")
                if not match_password(user.old_password,result.password):
                    raise UnauthorizedError(public_message="Incorrect Old password entered by the user",internal_message=f"Password cannot be change for user_id:{user_id} due to password mismatch")
                if match_password(user.new_password,user.old_password):
                   raise  ConflictError(public_message="New password should not match the past ones")
                
               
                result.password =  hash_password(user.new_password)
                
               
            return {"detail":f"User password has been changed {result.id}"}
    except (UnauthorizedError,AppError):
        raise
    except SQLAlchemyError as exc:
       raise translate_database_error(exc=exc) from exc
    except Exception as exc:
        raise AppError(error_code="UNEXPECTED_ERROR",status_code=500,internal_message=str(exc),public_message="An unexpected error has occured. Please login again") from exc


async def get_user_profile_service(session:AsyncSession,user_id:UUID):
    """Return the authenticated user's own account details.

    The user id always comes from a validated access token, so a missing row
    means the account was removed after the token was issued.
    """
    try:
        user = await find_user_by_user_id(session=session,user_id=user_id)
        if user is None:
            raise NotFoundError(
                public_message="User account not found",
                internal_message=f"No user account found for user_id={user_id}",
            )
        return user
    except (NotFoundError,AppError):
        raise
    except SQLAlchemyError as exc:
       raise translate_database_error(exc=exc) from exc
    except Exception as exc:
        raise AppError(error_code="UNEXPECTED_ERROR",status_code=500,internal_message=str(exc),public_message="An unexpected error has occured. Unable to fetch user details") from exc


