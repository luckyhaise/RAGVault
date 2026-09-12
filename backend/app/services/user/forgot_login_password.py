from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.database_errors import translate_database_error
from app.core.exceptions.email_exceptions import EmailDeliveryError
from app.core.exceptions.exceptions import ConflictError
from app.core.security import hash_password, match_password
from app.schemas.user_schema import ForgotPasswordChange
from app.services.helpers.find_user_username_email import (
    find_user_account_from_email_or_user_name,
)
from app.services.helpers.otp_helper import verify_otp


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
