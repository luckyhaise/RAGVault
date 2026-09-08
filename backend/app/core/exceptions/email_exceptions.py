from .exceptions import AppError


class EmailDeliveryError(AppError):
    def __init__(
        self,   
        internal_message: str | None = None,
        public_message: str = "We could not send your email right now. Please try again later shortly",
        error_code: str = "EMAIL_DELIVERY_ERROR",
        status_code: int = 503
    ):
        
        resolved_internal = internal_message or public_message
        
        super().__init__(
            public_message=public_message, 
            status_code=status_code, 
            internal_message=resolved_internal,
            error_code=error_code
        )
