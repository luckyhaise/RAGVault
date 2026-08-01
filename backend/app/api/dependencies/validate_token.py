from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from fastapi import Depends , HTTPException, status
from app.core.security import decode_access_token

security_scheme = HTTPBearer()

async def validate_token_and_get_user_id(credentials:HTTPAuthorizationCredentials= Depends(security_scheme)):

    try :
        user_id = decode_access_token(token=credentials.credentials)
        return user_id
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail=str(e))
    
