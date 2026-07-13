from fastapi.security import OAuth2PasswordBearer 
from fastapi import Depends , HTTPException, status
from app.core.security import decode_access_token

oauth =OAuth2PasswordBearer(tokenUrl="login")

async def validate_token_and_get_user_id(token:str = Depends(oauth)):
    try :
        user_id = decode_access_token(token=token)
        return user_id
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=str(e))
    
