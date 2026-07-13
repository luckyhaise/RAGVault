from fastapi import FastAPI , Request  , status
import logging

from fastapi.exceptions import RequestValidationError 
from starlette.exceptions import HTTPException as StarLetteHttpException
from fastapi.responses import JSONResponse
from .exceptions import AppError

logger = logging.getLogger(__name__)


async def app_error_handler(request:Request,exc:AppError)->JSONResponse:
    logger.warning("Application Error: %s %s | code=%s | message=%s | error_code= %s",request.method,
                   request.url.path,
                   exc.status_code,
                   exc.internal_message,
                   exc.error_code)
    return JSONResponse(status_code=exc.status_code,content={"error":{
        "code":exc.status_code,
        "error_code": exc.error_code,
        "message" : exc.public_message
    }})

async def validation_error_handler(request:Request,exc:RequestValidationError):
     errors:list[dict] = []
    
     for error in exc.errors():
      errors.append(
         {
             "field": ".".join(str(part) for part in error["loc"]),
             "message": error["msg"],
             "type": error["type"]

         }
      )
     logger.warning("Validation Error: %s %s | code=%s | message=%s | error_code = %s",
                    request.method,
                    request.url.path,
                    "422",
                     [error["message"] for error in errors],
                     "validation_error")
     return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,content={
         "error": {
            "code" : "validation_error",
            "message": "The submitted request data is invalid",
            "details": errors
         }
      })

async def http_exception_handler(request:Request,exc:StarLetteHttpException):
   return JSONResponse(status_code=exc.status_code,content={
      "error": {
       "code":"http_error",
      "message": exc.detail}
   })
async def unexpected_exception_handler(request:Request,exc:Exception):
    logger.exception(
        "Unhandled exception during %s %s | detail=%s",
        request.method,
        request.url.path,
        str(exc)
    )
    return JSONResponse(status_code=500, content={
       "error" : {
          "code" : "Internal server Error",
          "message" : "An unexpected server error occured"
       }
    })
def register_expection_handler(app:FastAPI) -> None:
   app.add_exception_handler(AppError,app_error_handler)
   app.add_exception_handler(RequestValidationError,validation_error_handler)
   app.add_exception_handler(StarLetteHttpException,http_exception_handler)
   app.add_exception_handler(Exception,unexpected_exception_handler)