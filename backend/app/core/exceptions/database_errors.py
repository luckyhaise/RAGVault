from sqlalchemy.exc import (
    SQLAlchemyError,
    IntegrityError,
    OperationalError,
    DataError,
    ProgrammingError,
)
from typing  import TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from .exceptions import AppError
T = TypeVar("T")
class DataBaseError(AppError):
    def __init__(self, public_message="A database Error Occured", status_code=500, internal_message:str|None = None, error_code="DATABASE_ERROR"):
        super().__init__(public_message = public_message, status_code = status_code, internal_message = internal_message, error_code = error_code)

def translate_database_error(exc:SQLAlchemyError) -> DataBaseError:
    if isinstance(exc,IntegrityError):
        return DataBaseError(
            public_message="The request conflicts with existing data",
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

async def run_database_operation(db:AsyncSession,operation:callable[[],T]) ->T :
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