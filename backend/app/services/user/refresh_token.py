from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions.database_errors import translate_database_error
from app.core.exceptions.exceptions import AppError, UnauthorizedError
from app.core.security import create_token, decode_token
from app.repositories.users_repository import find_user_session_by_user_id_for_update


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
