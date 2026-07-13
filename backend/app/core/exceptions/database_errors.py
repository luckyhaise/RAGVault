from sqlalchemy.exc import (
    SQLAlchemyError,
    IntegrityError,
    OperationalError,
    DataError,
    ProgrammingError,
)
import re
import logging
from typing  import TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from .exceptions import AppError

logger = logging.getLogger(__name__)

INTEGRITY_ERROR_MAP = {
    "uq_email": {
        "message": "An account with this email already exists.",
        "code": "EMAIL_ALREADY_EXISTS",
        "field": "email",
    },
    "uq_user_name": {
        "message": "This username is already taken.",
        "code": "USERNAME_ALREADY_EXISTS",
        "field": "user_name",
    },
    "uq_phone" : {
        "message": "An account already exists with this Phone Number",
        "code" : "PHONE_NUMBER_ALREADY_EXISTS",
        "field" : "phone"},
    "uq_document_idempotency_key": {
        "message": "A job already exists with this idempotancy key",
        "code" : "IDEMPOTANCY_KEY_ALREADY_EXISTS",
        "field" : "idempotancy_key"
    }
    }


def get_constraint_name(exc:IntegrityError) :
    original_error = exc.orig
    if (name := getattr(original_error,"constraint_name",None)):
        return name
    diagnostics = getattr(original_error,"diag",None)
    if diagnostics is not None :
        constraint_name = getattr(diagnostics,"constraint_name",None)
        if constraint_name:
         return constraint_name
        
    underlying_error = getattr(original_error,"__cause__",None)
    if underlying_error is not None:
        constraint_name = getattr(underlying_error,"constraint_name",None)
        if constraint_name:
            return constraint_name
        
    error_msg = str(original_error)
    if "constraint failed" in error_msg.lower():
        match = re.search(r"failed:\s+([a-zA-Z0-9_\.]+)", error_msg)
        if match:
            return match.group(1)
    return None
    





T = TypeVar("T")
class DataBaseError(AppError):
    def __init__(self, public_message="A database Error Occured", status_code=500, internal_message:str|None = None, error_code="DATABASE_ERROR"):
        super().__init__(public_message = public_message, status_code = status_code, internal_message = internal_message, error_code = error_code)

def translate_database_error(exc:SQLAlchemyError) -> DataBaseError:
    if isinstance(exc,IntegrityError):
        constraint_voilated = get_constraint_name(exc=exc)
        error_info = INTEGRITY_ERROR_MAP.get(constraint_voilated or "")
        if error_info is not None:
            return DataBaseError(
                public_message=error_info["message"],
                error_code=error_info["code"],
                status_code=409,
                internal_message=str(exc)

            )
        return DataBaseError(
            public_message= "The request conflicts with existing data",
            internal_message= str(exc),
            status_code=409,
            error_code="DATABASE_INTEGRITY_ERROR"
        
        )
    if isinstance(exc,OperationalError):
        return DataBaseError(
            public_message="Database service is temporarily unavilable",
            internal_message=str(exc),
            status_code=503,
            error_code="DATABASE_OPERATIONAL_ERROR"

        )
    if isinstance(exc,DataError):
        return DataBaseError(
            public_message= "Invalid data was provided",
            internal_message= str(exc),
            status_code= 400,
            error_code= "DATABASE_DATA_ERROR"
        )
    if isinstance(exc,ProgrammingError):
        return DataBaseError(public_message="An unexpected error occured while trying to process your request",
                            internal_message= str(exc),
                            error_code= "DATABASE_PROGRAMMING_ERROR",
                            status_code=500
                            )
    return DataBaseError(public_message="Something went wrong. Please try again later",
                         internal_message= str(exc),
                         error_code="SQL_ALCHEMY_ERROR",
                         status_code=500
                         )

async def  run_database_operation(session:AsyncSession,operation:callable[[],T]) ->T :
    """
    Runs a database operation safely.

    If sql alchemy error happens:
    - Rollback the session
    - Convert sql alchemy Error into AppError
    - Raise the error
    """
    try: 
        return await operation()
    except SQLAlchemyError as exc:
        raise translate_database_error(exc=exc) from exc
    


