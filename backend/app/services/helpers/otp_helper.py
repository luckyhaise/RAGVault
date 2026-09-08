import secrets
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions.database_errors import (
    SQLAlchemyError,
    translate_database_error,
)
from app.core.exceptions.email_exceptions import EmailDeliveryError
from app.core.exceptions.exceptions import AppError
from app.core.security import hash_password, match_password
from app.infrastructure.redis.rate_limit import (
    redis_check_user_rate_limit,
    redis_verification_attempt_limit,
)
from app.repositories.otp_repository import delete_otp, get_saved_otp, save_otp
from app.services.email_service import send_otp_email


async def otp_request_hanlder_for_user_service(
    session: AsyncSession,  email: str,purpose:Literal["login","create_account"] = "login",
)-> tuple[UUID|None,str]:
   
    try:
        expire_at = datetime.now(UTC) + timedelta(
            minutes=settings.otp_expire_minutes
        )
        otp = "".join(secrets.choice("0123456789") for _ in range(6))
        limit = settings.create_account_attempts if purpose == "create_account" else settings.log_in_attempts
        window = settings.create_account_block_window_sec if purpose == "create_account"  else settings.log_in_block_window_sec
        approved = await redis_check_user_rate_limit(key=f"otp:request:{email}",limit=limit,window=window)
        if approved is not True:
            raise EmailDeliveryError(public_message=f"Otp request limit exhausted. Please try after {window / 60}",status_code=429,error_code="OTP_RATE_LIMIT_EXCEEDED")

        saved_otp = await save_otp(
            
                session=session,
                email=email,
                otp_hash=hash_password(otp),
                expires_at=expire_at,
                
            )
            
        await session.commit()
        
        result = send_otp_email.delay(recipient_email=email,otp=otp)# pyright: ignore[reportFunctionMemberAccess]
       
        task_id:str = result.id
        return saved_otp.id , task_id 

    except (AppError, EmailDeliveryError):
            
            raise
    except Exception as exc:
        await session.rollback()
        public_message = "Unexpected error occured, Please try again"
        error_code = "UNEXPECTED_ERROR"
        status_code = 500
        
        if isinstance(exc, SQLAlchemyError):
            error = translate_database_error(exc=exc)
            internal_message = error.internal_message
            public_message = error.public_message
            error_code = error.error_code
            status_code = error.status_code

        else:
            internal_message = str(exc)

        raise AppError(internal_message=internal_message,public_message=public_message,status_code=status_code,error_code=error_code)





async def verify_otp(session:AsyncSession,otp:str,otp_id:UUID,email:str,purpose:Literal["login","create_account"] = "login"):
        try:
            retrieved_otp = await get_saved_otp(session=session,otp_id=otp_id)
            if retrieved_otp is None:
                raise EmailDeliveryError(public_message="Unexpected error occured, Please try again later",internal_message=f"Unable to find otp from otp if {otp_id}",error_code="UNEXPECTED_ERROR",status_code=500)
            if retrieved_otp.email != email:
                raise EmailDeliveryError(public_message="Some unexpected error occured in OTP Verification. Please try again later",internal_message=f"OTP id email does not match with verificaton request email {retrieved_otp.email} != {email}  ",status_code=400,)
            if retrieved_otp.expires_at < datetime.now(UTC):
                await delete_otp(otp_id=otp_id,session=session)
                await session.commit()
                raise EmailDeliveryError(public_message="Otp has been expired. Please retry a new OTP",error_code="OTP_EXPIRED",status_code=400)
            limit = settings.create_account_attempts if purpose == "create_account" else settings.log_in_attempts
            allowed =await  redis_verification_attempt_limit(key=f"otp:verification:{otp_id}",limit=limit)
            if allowed is not True:
                    await delete_otp(otp_id=otp_id,session=session)
                    await session.commit()
                    raise EmailDeliveryError(public_message="OTP verification attempts failed, Please request a new OTP",
                        error_code="OTP_VERIFICATION_ATTEMPTS_EXCEEDED",
                           status_code=429,)
            
            if match_password(hashed_password=retrieved_otp.otp_hash,password=otp) is True:
                await delete_otp(otp_id=otp_id,session=session)
                await session.commit()
                return True
            else:
                return False 
        except (EmailDeliveryError, AppError):
            raise
            
        except Exception as exc:
            await session.rollback()
            public_message = "Unexpected error occured, Please try again"
            error_code = "UNEXPECTED_ERROR"
            status_code = 500
            
            if isinstance(exc, SQLAlchemyError):
                error = translate_database_error(exc=exc)
                internal_message = error.internal_message
                public_message = error.public_message
                error_code = error.error_code
                status_code = error.status_code
    
            else:
                internal_message = str(exc)
    
            raise AppError(internal_message=internal_message,public_message=public_message,status_code=status_code,error_code=error_code)
            



