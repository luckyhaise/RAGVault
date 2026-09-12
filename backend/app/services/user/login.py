import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.database_errors import translate_database_error
from app.core.exceptions.exceptions import UnauthorizedError
from app.core.security import create_token, match_password
from app.repositories.users_repository import (
    create_session,
    find_user_by_email,
    find_user_by_user_name,
)
from app.schemas.user_schema import UserLogin

logger = logging.getLogger(__name__)


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
