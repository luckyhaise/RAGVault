from argon2 import PasswordHasher
from uuid import UUID
from jose import jwt 
from jose.exceptions import JWTError
from datetime import date, datetime,timedelta , UTC
from app.core.config import settings
from typing import Any



hasher = PasswordHasher()


def hash_password(password: str):
    hashed_password = hasher.hash(password=password)
    return hashed_password


def match_password(password: str, hashed_password: str):
    return hasher.verify(hash=hashed_password, password=password)

def create_access_token(subject: str) -> str:
    now = datetime.now(UTC)
    expire_at = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload:dict[str, Any] = {
        "sub" : str(subject),
        "iat" : int(now.timestamp()),
        "exp" : int(expire_at.timestamp())
    }
    token = jwt.encode(payload,key=settings.jwt_secret_key,algorithm=settings.jwt_algorithm)
    return token 
    
def decode_access_token(token:str)-> str:
   decoded =  jwt.decode(token=token,
       key= settings.jwt_secret_key,
       algorithms= [settings.jwt_algorithm]
     
    )
   user_id = decoded.get("sub")
   if user_id is None:
       raise JWTError("This token does not contain a user id")
   return user_id


