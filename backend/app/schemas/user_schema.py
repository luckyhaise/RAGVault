from tokenize import single_quoted

from pydantic import BaseModel, Field ,  EmailStr , model_validator , ConfigDict ,  AfterValidator
from uuid import UUID
from typing import  Annotated , Self
from app.core.config import settings
import re

USERNAME_PATTERN = r"^[a-zA-Z0-9_.-]+$"
PASSWORD_PATTERN = re.compile(settings.regex)

SPECIAL_CHARACTERS = "@#_!$%*.-"


def validate_new_password(password: str) -> str:
    if not PASSWORD_PATTERN.fullmatch(password):
        raise ValueError(
            "Password contains invalid characters. "
            "Only alphanumeric characters and @#_!$%*.- are allowed"
        )

    if not any(character.isupper() for character in password):
        raise ValueError(
            "At least one character must be uppercase"
        )

    if not any(character.islower() for character in password):
        raise ValueError(
            "At least one character must be lowercase"
        )

    if not any(character.isdigit() for character in password):
        raise ValueError(
            "At least one character must be a digit"
        )

    if not any(
        character in SPECIAL_CHARACTERS
        for character in password
    ):
        raise ValueError(
            "At least one special character is required"
        )

    return password


NewPassword = Annotated[
    str,
    Field(min_length=8, max_length=128),
    AfterValidator(validate_new_password),
]
def validate_phone_number(phone:str):
    if not phone.startswith("+") :
        raise ValueError("Phone number must contain country code")
    if not len(phone[1:]) >= 7:
        raise ValueError("Phone number is too small")
    if not len(phone[1:]) <= 15:
        raise ValueError("Phone number is too large")
    return phone

PhoneStr = Annotated[str,Field(
        pattern=r"^\+[1-9][0-9]+$",
    ),AfterValidator(validate_phone_number)]

class UserLogin(BaseModel):
    user_name: str | None = Field(
        default=None,
        pattern=USERNAME_PATTERN,
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
    user_name: str = Field(
        min_length=3,
        max_length=200,
        pattern=USERNAME_PATTERN,
    )
    email: EmailStr
    password: NewPassword

    name: str = Field(
        min_length=2,
        max_length=100,
    )
    phone: PhoneStr
    
class UserCreate(BaseModel):
    user_name: str = Field(
        min_length=3,
        max_length=200,
        pattern=USERNAME_PATTERN,
    )
    email: EmailStr
    password: NewPassword
    otp_id:UUID
    
    name: str = Field(
        min_length=2,
        max_length=100,
    )
    phone: PhoneStr
    otp:str = Field(min_length=6,max_length=6)
    
class UserCreateRequestResponse(BaseModel):
    otp_id: UUID
    task_id : UUID
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

class UserCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    email: EmailStr 
    id : UUID
    name: str 
class RequestCreateAccountResponse(BaseModel):
    otp_id:UUID
    task_id:UUID
class ForgotPasswordRequestResponse(BaseModel):
    otp_id:UUID
    task_id:UUID
class UserLoginResponse(BaseModel):
    access_token:str 