from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions.exceptions import UnauthorizedError

hasher = PasswordHasher()


def hash_password(password: str):
    hashed_password = hasher.hash(password=password)
    return hashed_password


def match_password(password: str, hashed_password: str):
     try : 
      return hasher.verify(hash=hashed_password, password=password)
     except VerifyMismatchError:
         return False
@dataclass
class TokenResult:
    access_token: str
    refresh_token: str | None
    refresh_expires_at: datetime | None
    refresh_jti: UUID | None
   


def create_token(subject: str,create_refresh_token:bool=False)  :
    now = datetime.now(UTC)
    expire_at = now + timedelta(minutes=settings.access_token_expire_minutes)
    access_payload:dict[str, Any] = {
        "sub" : str(subject),
        "iat" : int(now.timestamp()),
        "exp" : int(expire_at.timestamp()),
        "jti": str(uuid4()),  
         "type": "access"
    }
    access_token = jwt.encode(access_payload,key=settings.jwt_secret_key,algorithm=settings.jwt_algorithm)
    if  create_refresh_token is True:
        refresh_expire_at=  now + timedelta(days=settings.refresh_token_expire_days)
        jti = uuid4()
        refresh_payload = {
            "sub": str(subject),
            "iat": int(now.timestamp()),
            "exp" : int(refresh_expire_at.timestamp()),
            "type":"refresh",
            "jti":str(jti)
            
        }
        refresh_token = jwt.encode(refresh_payload,key=settings.jwt_secret_key,algorithm=settings.jwt_algorithm)
        return TokenResult(
            access_token=access_token,
            refresh_expires_at=refresh_expire_at,
            refresh_jti=jti,
            refresh_token=refresh_token
        )
    return TokenResult(
        access_token=access_token,refresh_expires_at=None,refresh_jti=None,refresh_token=None
    )
    
def decode_token(token:str,expected_type:str):
    try:
        payload = jwt.decode(token, key=settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    
        
        if payload.get("type") != expected_type:
            raise UnauthorizedError(
                public_message = "Your login session is invalid or expired. Please sign in.",

                internal_message=f"Invalid token type. Expected {expected_type} token."
            )
        if datetime.fromtimestamp(payload["exp"] ,tz=UTC) < datetime.now(UTC):
                raise UnauthorizedError(internal_message="Refresh token send to refesh_token_service is Expired",
                    public_message="Your session is invalid please login again")

        
        return payload
        
    except JWTError as exc:
        raise UnauthorizedError(
            public_message = "Your login session is invalid or expired. Please sign in.",
            internal_message="Could not validate credentials or token has expired",
            
        ) from exc
