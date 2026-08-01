import pytest
from unittest.mock import AsyncMock
import asyncio
from app.core.exceptions.database_errors import (
    get_constraint_name, run_database_operation,translate_database_error, DataBaseError
)
from sqlalchemy.exc import (
    SQLAlchemyError,
    IntegrityError,
    OperationalError,
    DataError,
    ProgrammingError,
    DatabaseError
)

def make_integrity_error(orig):
    return IntegrityError(
        statement="INSERT INTO users VALUES (:email)",
        params={"email": "test@example.com"},
        orig=orig,
    )

def make_database_exception(
    exception_type: type[SQLAlchemyError],
     constraint_name = None,
) -> SQLAlchemyError:
    """
    Construct a SQLAlchemy database exception without using a real database.
    """
    class FakeDiag:
        def __init__(self, constraint_name):
            self.constraint_name = constraint_name
    # class FakeOrig(Exception):
    #     def __init__(self, constraint_name):
    #         self.daig = FakeDiag(constraint_name)

    return exception_type(
        statement="INSERT INTO users (email) VALUES (:email)",
        params={"email": "test@example.com"},
        orig=FakeDiag(constraint_name),
    )


@pytest.mark.parametrize(
    ("exc_type", "public_message", "error_code", "status_code"),
    [
        (IntegrityError,
         "The request conflicts with existing data",
         "DATABASE_INTEGRITY_ERROR",
         409),
        (
            OperationalError,
            "Database service is temporarily unavilable",
            "DATABASE_OPERATIONAL_ERROR",
            503,
        ),
        (
            DataError,
            "Invalid data was provided",
            "DATABASE_DATA_ERROR",
            400,
        ),
        (
            ProgrammingError,
            "An unexpected error occured while trying to process your request",
            "DATABASE_PROGRAMMING_ERROR",
            500,

        ),
        (DatabaseError,
         "Something went wrong. Please try again later",
         "SQL_ALCHEMY_ERROR",
         500
         )
        
    ],
)
def test_database_error_is_translated(exc_type, public_message, error_code, status_code):
    error = make_database_exception(exc_type)
    translated = translate_database_error(error)

    assert getattr(translated, "public_message") == public_message
    assert getattr(translated, "error_code") == error_code
    assert getattr(translated, "status_code") == status_code

@pytest.mark.parametrize(
        ("constraint","message","code"),[
            ("uq_email",
        "An account with this email already exists.",
        "EMAIL_ALREADY_EXISTS",
        ),
        (  "uq_user_name",
        "This username is already taken.",
        "USERNAME_ALREADY_EXISTS",
        ),
        (    "uq_phone",
        "An account already exists with this Phone Number",
        "PHONE_NUMBER_ALREADY_EXISTS",
        ),
        ( "uq_document_idempotency_key",
        "A job already exists with this idempotancy key",
        "IDEMPOTANCY_KEY_ALREADY_EXISTS",
        ),
        ("uq_random_constraint_that_dosent_exists",
          "The request conflicts with existing data",
          "DATABASE_INTEGRITY_ERROR"
         )
        ])
def test_constraint_name_errors_handled(constraint,message,code):
    error = make_database_exception(IntegrityError,constraint)
    translated = translate_database_error(error)
    assert getattr(translated,"public_message") == message
    assert getattr(translated,"error_code") == code
    assert getattr(translated,"status_code") == 409
@pytest.mark.asyncio 
async def test_run_database_operation_sucess():
    session = AsyncMock()
    async def operation():
        return 42+23
    result = await run_database_operation(operation=operation,session=session)
    assert result == 42+23

@pytest.mark.asyncio
async def test_run_database_rollback_check():
    session = AsyncMock()

    async def operation():
        raise make_database_exception(IntegrityError)
    
    with pytest.raises(DataBaseError):
        await run_database_operation(session, operation)
    
    session.rollback.assert_awaited_once()
@pytest.mark.asyncio
async def test_run_database_operation_translates_error():
    session = AsyncMock()
    async def operation(): 
        raise make_database_exception(IntegrityError)
    with pytest.raises(DataBaseError) as excinfo:
      await run_database_operation(session=session,operation=operation)
    assert excinfo.value.status_code == 409
    assert excinfo.value.error_code == "DATABASE_INTEGRITY_ERROR"

@pytest.mark.asyncio
async def test_run_database_error_exception_chaining():
    session = AsyncMock()
    async def operation(): 
        raise make_database_exception(IntegrityError)
    with pytest.raises(DataBaseError) as excinfo:
      await run_database_operation(session=session,operation=operation)
    assert isinstance(excinfo.value.__cause__,IntegrityError) 


import pytest
from sqlalchemy.exc import IntegrityError

@pytest.mark.parametrize(
    ("orig", "expected_constraint"),
    [
    
        (
            type(
                "FakeOrig",
                (),
                {"constraint_name": "uq_email"},
            )(),
            "uq_email",
        ),

       
        (
            type(
                "FakeOrig",
                (),
                {
                    "diag": type(
                        "FakeDiag",
                        (),
                        {"constraint_name": "uq_user_name"},
                    )()
                },
            )(),
            "uq_user_name",
        ),

       
        (
            type(
                "FakeOrig",
                (),
                {
                    "__cause__": type(
                        "FakeCause",
                        (),
                        {"constraint_name": "uq_phone"},
                    )()
                },
            )(),
            "uq_phone",
        ),

    
        (
            object(),
            None,
        ),
    ],
)
def test_get_constraint_name(orig, expected_constraint):
    error = make_integrity_error(orig)

    assert get_constraint_name(error) == expected_constraint