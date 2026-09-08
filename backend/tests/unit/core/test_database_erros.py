import pytest
from sqlalchemy.exc import (
    DatabaseError,
    DataError,
    IntegrityError,
    OperationalError,
    ProgrammingError,
    SQLAlchemyError,
)

from app.core.exceptions.database_errors import (
    get_constraint_name,
    translate_database_error,
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

    assert translated.public_message == public_message
    assert translated.error_code == error_code
    assert translated.status_code == status_code
    assert translated.internal_message == str(error)

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
    assert translated.public_message == message
    assert translated.error_code == code
    assert translated.status_code == 409


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

def test_translate_database_error_uses_orig_constraint_name():
    orig = type("FakeOrig", (), {"constraint_name": "uq_email"})()
    error = make_integrity_error(orig)
    translated = translate_database_error(error)

    assert translated.public_message == "An account with this email already exists."
    assert translated.error_code == "EMAIL_ALREADY_EXISTS"
    assert translated.status_code == 409
