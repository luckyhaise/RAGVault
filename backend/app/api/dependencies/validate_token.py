from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from fastapi import Depends , HTTPException, status
from app.core.security import decode_token

security_scheme = HTTPBearer()

async def validate_token_and_get_user_id(credentials:HTTPAuthorizationCredentials= Depends(security_scheme)):

    try :
        payload = decode_token(token=credentials.credentials,expected_type="access")
        return payload["sub"]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid session. Please login again")
    
async def validate_token_for_refresh(credentials:HTTPAuthorizationCredentials= Depends(security_scheme)):
    return credentials.credentials