# from sqlalchemy.exc import DatabaseError, SQLAlchemyError , IntegrityError

class AppError(Exception):
    def __init__(self,
                 public_message : str,
                 status_code: int,
                 internal_message:str,
                 error_code = "App_error"
                 ):
        self.public_message = public_message
        self.status_code = status_code
        self.internal_message = internal_message or public_message
        self.error_code = error_code
        super().__init__(self.internal_message)


class NotFoundError(AppError):
    def __init__(self,internal_message:str|None = None,
                public_message = "Resource Not Found",
                status_code=404,

                ):
                super().__init__(public_message=public_message, 
                status_code=status_code,
                internal_message=internal_message)


class ConflictError(AppError):
      def __init__(self,internal_message:str|None = None,
                    public_message = "Resource already exists"):
            super().__init__(public_message = public_message , status_code = 409, internal_message = internal_message, error_code="CONFLICT")

class ForbiddenError(AppError):
      def __init__(self, internal_message:str|None = None,public_message = "You do not have permission to perform this action",  error_code="App_error"):
            super().__init__(public_message, status_code = 403, internal_message= internal_message, error_code="FORBIDDEN")


class UnauthorizedError(AppError):
    def __init__(
        self,
        public_message: str = "You are not authorized.",
        internal_message: str | None = None,
    ):
        super().__init__(
            public_message=public_message,
            status_code=401,
            internal_message=internal_message,
            error_code="UNAUTHORIZED",
        )
class ValidationAppError(AppError):
    def __init__(
        self,
        public_message: str = "Invalid input.",
        internal_message: str | None = None,
    ):
        super().__init__(
            public_message=public_message,
            status_code=400,
            internal_message=internal_message,
            error_code="VALIDATION_ERROR",
        )
class ExternalServiceError(AppError):
    def __init__(
        self,
        public_message: str = "External service is currently unavailable.",
        internal_message: str | None = None,
    ):
        super().__init__(
            public_message=public_message,
            status_code=503,
            internal_message=internal_message,
            error_code="EXTERNAL_SERVICE_ERROR",
        )

