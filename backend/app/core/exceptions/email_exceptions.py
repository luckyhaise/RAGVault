from .exceptions import AppError

class EmailDeliveryError(AppError):
    def __init__(self,   internal_message:str|None = None
                 ,public_message = "We could not send your email right now. Please try again later shortly",
                  error_code="EMAIL_DELIVERY_ERROR",
                  status_code = 503):
        super().__init__(public_message = public_message
                         , status_code = status_code, internal_message = internal_message,
                           error_code= error_code)
        

