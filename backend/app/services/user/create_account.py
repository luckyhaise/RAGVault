import logging
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.database_errors import translate_database_error
from app.core.exceptions.email_exceptions import EmailDeliveryError
from app.core.security import hash_password
from app.repositories.users_repository import save_user
from app.schemas.user_schema import UserCreate
from app.services.helpers.otp_helper import verify_otp

logger = logging.getLogger(__name__)


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
