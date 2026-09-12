from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.exceptions import (
    UnauthorizedError,
    ValidationAppError,
)
from app.models.models import Users
from app.repositories.users_repository import (
    find_user_by_email,
    find_user_by_user_name,
)





async def find_user_account_from_email_or_user_name(session:AsyncSession,user_name:str|None,email:str|None) -> Users:
    if user_name is not None:
        user_detail = await find_user_by_user_name(session=session,user_name=user_name)
    elif email is not None:
        user_detail = await find_user_by_email(session=session,email=email)
    else:
        raise ValidationAppError(public_message="Please enter email or user name")
    if user_detail is None:
        raise UnauthorizedError(internal_message=f"Account Not found. User_name:{user_name} User_email:{email} ",
            public_message="Invalid username/email or password")
    return user_detail
