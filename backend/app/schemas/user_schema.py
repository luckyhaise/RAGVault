from pydantic import BaseModel, Field ,  EmailStr , model_validator , ConfigDict , field_validator
from uuid import UUID
from typing import Literal
from app.core.config import settings

class User_Login(BaseModel):
    user_name:str|None = Field(pattern=settings.regex,description="Name of the user",default=None)
    email : EmailStr|None = Field(description="Email of the User",default=None)
    password:str = Field(..., description="Password of the user", pattern=settings.regex) 
    @model_validator(mode="after")
    def email_or_phone(self):
        if not self.user_name and not self.email:
            raise ValueError("Provide either email or phone number")
        return self 
    @field_validator("password")
    @classmethod
    def validate_password(cls,password:str) -> str:
        special_characters = list("@#_!$%*.-")
        if not any(char.isupper() for char in password):
            raise ValueError("Atleast One character should be upper")
        if not any(char.islower() for char in password):
            raise ValueError("Atleast one character should be lower")
        if not any(char.isdigit() for char in password):
            raise ValueError("Atleast One character should be a number")
        if not any(char in special_characters for char in password):
            raise ValueError(f"Aleast one character should be a special character {special_characters}")
        return password


# class Forgot_Password()

class User_Create(User_Login):
    name: str = Field(...,description="Name of the user",min_length=2,max_length=100)
    phone: str  = Field(description="Phone number of the user")

    @model_validator(mode="after")
    def validate_phoneno(self):
        if self.phone[0] != "+":
            raise ValueError("Country code should be included in the phone number")
        if len(self.phone[3:]) < 10:
            raise ValueError("Phone number should be atleast 10 digits long") 
        return self
    

class UserCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    email: EmailStr 
    id : UUID
    name: str 
