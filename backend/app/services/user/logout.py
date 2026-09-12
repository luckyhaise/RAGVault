from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.database_errors import translate_database_error
from app.core.exceptions.exceptions import AppError, UnauthorizedError
from app.core.security import decode_token
from app.repositories.users_repository import find_user_session_by_user_id_for_update


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
