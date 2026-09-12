
import re
from datetime import datetime
from typing import Annotated, Self , Literal
from uuid import UUID

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
)

from app.core.config import settings
from sqlalchemy.sql.compiler import _BaseCompilerStackEntry

USERNAME_PATTERN = r"^[a-zA-Z0-9_.-]+$"
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 200
USERNAME_RE = re.compile(USERNAME_PATTERN)
PASSWORD_PATTERN = re.compile(settings.regex)

SPECIAL_CHARACTERS = "@#_!$%*.-"


def validate_new_password(password: str) -> str:
    if not PASSWORD_PATTERN.fullmatch(password):
        raise ValueError(
            "Password contains invalid characters. "
            "Password can only alphanumeric characters and @ # _ ! $ % * . -"
        )

    if not any(character.isupper() for character in password):
        raise ValueError(
            "Password must have atleast one uppercase character"
        )

    if not any(character.islower() for character in password):
        raise ValueError(
            "Password must have atleast one lowercase character"
        )

    if not any(character.isdigit() for character in password):
        raise ValueError(
            "Password must have atleast one digit"
        )

    if not any(
        character in SPECIAL_CHARACTERS
        for character in password
    ):
        raise ValueError(
            "Password must have atleast one special character"
        )

    return password


NewPassword = Annotated[
    str,
    Field(min_length=8, max_length=128),
    AfterValidator(validate_new_password),
]


def validate_new_username(user_name: str) -> str:
    if not USERNAME_RE.fullmatch(user_name):
        raise ValueError(
            "Username contains invalid characters. "
            "Username can only contain letters, numbers, and . _ -"
        )

    if not any(character.isalpha() for character in user_name):
        raise ValueError(
            "Username must have atleast one letter"
        )

    if not any(character.isdigit() for character in user_name):
        raise ValueError(
            "Username must have atleast one number"
        )

    return user_name


NewUsername = Annotated[
    str,
    Field(min_length=USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH),
    AfterValidator(validate_new_username),
]


class UserLogin(BaseModel):
    user_name: str | None = Field(
        default=None,
    )
    email: EmailStr | None = None
    password: str = Field(
        min_length=1,
        max_length=128,
    )

    @model_validator(mode="after")
    def require_login_identifier(self) -> Self:
        if not self.user_name and not self.email:
            raise ValueError(
                "Provide either email or username"
            )
        if self.user_name  and self.email:
            raise ValueError("Provide only username or email")
        return self


class UserCreateRequest(BaseModel):
    user_name: NewUsername
    email: EmailStr
    password: NewPassword

    name: str = Field(
        min_length=2,
        max_length=100,
    )
 
    
class UserCreate(BaseModel):
    user_name: NewUsername
    email: EmailStr
    password: NewPassword
    otp_id:UUID
    
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    otp:str = Field(min_length=6,max_length=6)

class ForgotPasswordRequest(BaseModel):
    user_name: str | None = Field(
        default=None,
        pattern=USERNAME_PATTERN,
    )
    email: EmailStr | None = None
class ForgotPasswordChange(BaseModel):
    user_name: str | None = Field(
        default=None,
        pattern=USERNAME_PATTERN,
    )
    email: EmailStr | None = None
    new_password:NewPassword
    otp:str = Field(min_length=6,max_length=6)
    otp_id:UUID
    @model_validator(mode="after")
    def require_login_identifier(self) -> Self:
        if not self.user_name and not self.email:
            raise ValueError(
                "Provide either email or username"
            )
        return self  
class ResetPassword(BaseModel):
    old_password:str
    new_password:NewPassword
class ChangeUserDetail(BaseModel):
    field: Literal["user_name","email","name"]
    new_value :str
    password:str = Field(min_length=1)
    @model_validator(mode="after")
    def validate_detail(self)-> Self:
        if self.field == "email":
            class ValidateEmail(BaseModel):
                email:EmailStr
            ValidateEmail(email=self.new_value)
        if self.field =="name":
            if len(self.new_value.strip()) < 2:
                raise ValueError("Name must be atleast 2 characters long")
            elif len(self.new_value.strip()) > 100:
                raise ValueError("Name must be less than 100 characters long")
        if self.field == "user_name":
            class ValidateUsername(BaseModel):
                user_name: NewUsername 
            ValidateUsername(user_name=self.new_value)            
        return self 
        
    

    
class UserCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    email: EmailStr 
    id : UUID
    name: str 
class CreateAccountRequestResponse(BaseModel):
    otp_id:UUID
    task_id:UUID
class ForgotPasswordRequestResponse(BaseModel):
    otp_id:UUID
    task_id:UUID


class LoginResponse(BaseModel):
    access_token:str
    refresh_token:str

class RefreshTokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    access_token:str =   Field(
        ...,
        min_length=1,
        description="JWT access token"
    )
    refresh_token:str|None = Field(...,min_length=1,description="JWT refresh token")


class UserProfileResponse(BaseModel):
    """The authenticated user's own account details."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID = Field(description="Unique identifier of the user")
    user_name: str = Field(description="The user's username")
    name: str = Field(description="The user's display name")
    email: EmailStr = Field(description="The user's email address")
    created_at: datetime = Field(description="Time when the account was created")
    updated_at: datetime = Field(description="Time when the account was last updated")
