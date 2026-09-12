from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.database_errors import translate_database_error
from app.core.exceptions.exceptions import AppError, NotFoundError
from app.repositories.users_repository import find_user_by_user_id


async def get_user_profile_service(session:AsyncSession,user_id:UUID):

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
