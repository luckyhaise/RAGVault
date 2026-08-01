import pytest

from app.core.exceptions.exceptions import (
    AppError,
    ConflictError,
    ExternalServiceError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    DataBaseError,
    ValidationAppError,
)
from app.core.exceptions.email_exceptions import EmailDeliveryError


def test_app_error_stores_all_values() -> None:
    error = AppError(
        public_message="Something went wrong",
        status_code=500,
        internal_message="Detailed internal information",
        error_code="INTERNAL_ERROR",
    )

    assert error.public_message == "Something went wrong"
    assert error.status_code == 500
    assert error.internal_message == "Detailed internal information"
    assert error.error_code == "INTERNAL_ERROR"


def test_app_error_uses_internal_message_as_exception_message() -> None:
    error = AppError(
        public_message="Safe public message",
        status_code=500,
        internal_message="Sensitive debugging information",
        error_code="INTERNAL_ERROR",
    )

    assert str(error) == "Sensitive debugging information"
    assert error.args == ("Sensitive debugging information",)


def test_app_error_falls_back_to_public_message() -> None:
    error = AppError(
        public_message="Safe public message",
        status_code=500,
        internal_message=None,  # type: ignore[arg-type]
        error_code="INTERNAL_ERROR",
    )

    assert error.internal_message == "Safe public message"
    assert str(error) == "Safe public message"


@pytest.mark.parametrize(
    (
        "exception_type",
        "expected_status_code",
        "expected_public_message",
        "expected_error_code",
    ),
    [
        (
            NotFoundError,
            404,
            "Resource Not Found",
            "App_error",
        ),
        (EmailDeliveryError,
         503,
         "We could not send your email right now. Please try again later shortly",
         "EMAIL_DELIVERY_ERROR",
         ),
        (
            ConflictError,
            409,
            "Resource already exists",
            "CONFLICT",
        ),(
            DataBaseError,
            500,
            "A database Error Occured",
            "DATABASE_ERROR"
        ),
        (
            ForbiddenError,
            403,
            "You do not have permission to perform this action",
            "FORBIDDEN",
        ),
        (
            UnauthorizedError,
            401,
            "You are not authorized.",
            "UNAUTHORIZED",
        ),
        (
            ValidationAppError,
            400,
            "Invalid input.",
            "VALIDATION_ERROR",
        ),
        (
            ExternalServiceError,
            503,
            "External service is currently unavailable.",
            "EXTERNAL_SERVICE_ERROR",
        ),
    ],
)
def test_exception_default_values(
    exception_type: type[AppError],
    expected_status_code: int,
    expected_public_message: str,
    expected_error_code: str,
) -> None:
    error = exception_type()

    assert isinstance(error, AppError)
    assert isinstance(error, Exception)
    assert error.status_code == expected_status_code
    assert error.public_message == expected_public_message
    assert error.error_code == expected_error_code

    # Because no internal message was supplied, AppError uses the public one.
    assert error.internal_message == expected_public_message
    assert str(error) == expected_public_message


@pytest.mark.parametrize(
    "exception_type",
    [
        NotFoundError,
        ConflictError,
        ForbiddenError,
        UnauthorizedError,
        ValidationAppError,
        EmailDeliveryError,
        ExternalServiceError,
        DataBaseError,
    ],
)
def test_exception_preserves_internal_message(
    exception_type: type[AppError],
) -> None:
    error = exception_type(
        internal_message="Detailed internal debugging message",
    )

    assert error.internal_message == "Detailed internal debugging message"
    assert str(error) == "Detailed internal debugging message"


@pytest.mark.parametrize(
    "exception_type",
    [
        NotFoundError,
        ConflictError,
        ForbiddenError,
        DataBaseError,
        UnauthorizedError,
        ValidationAppError,
        ExternalServiceError,
        EmailDeliveryError,
    ],
)
def test_exception_allows_custom_public_message(
    exception_type: type[AppError],
) -> None:
    error = exception_type(
        public_message="Custom client-facing message",
    )

    assert error.public_message == "Custom client-facing message"
    assert error.internal_message == "Custom client-facing message"


def test_subclass_can_be_caught_as_app_error() -> None:
    with pytest.raises(AppError) as captured:
        raise NotFoundError(
            internal_message="Document 123 was not found",
        )

    assert isinstance(captured.value, NotFoundError)
    assert captured.value.status_code == 404
    assert str(captured.value) == "Document 123 was not found"