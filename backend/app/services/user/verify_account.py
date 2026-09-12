from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.exceptions import ValidationAppError
from app.schemas.user_schema import ForgotPasswordRequest, UserCreateRequest
from app.services.helpers.find_user_username_email import (
    find_user_account_from_email_or_user_name,
)
from app.services.helpers.otp_helper import otp_request_hanlder_for_user_service


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
