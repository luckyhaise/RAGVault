from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions.exceptions import UnauthorizedError
from app.core.security import decode_token

security_scheme = HTTPBearer()

async def validate_token_and_get_user_id(credentials:HTTPAuthorizationCredentials= Depends(security_scheme))-> str :

    try :
        payload = decode_token(token=credentials.credentials,expected_type="access")
        return payload["sub"]
    except Exception as exc:
        raise UnauthorizedError(public_message="Invalid session. Please login again",internal_message=str(exc)) from exc
    
async def validate_token_for_refresh(credentials:HTTPAuthorizationCredentials= Depends(security_scheme)):
    return credentials.credentials