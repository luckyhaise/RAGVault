from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions.database_errors import translate_database_error
from app.core.exceptions.exceptions import AppError, ConflictError, UnauthorizedError
from app.core.security import hash_password, match_password
from app.infrastructure.redis.rate_limit import redis_check_user_rate_limit
from app.repositories.users_repository import reset_password
from app.schemas.user_schema import ResetPassword


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
