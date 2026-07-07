from pydantic import BaseModel, Field , model_validato , EmailStr , model_validator
from uuid import UUID
from typing import Literal

class User_Login(BaseModel):
    user_name:str|None = Field(pattern=r"^[0-9a-zA-Z]+$",description="Name of the user",default=None)
    email : EmailStr|None = Field(description="Email of the User",default=None)
    password:str = Field(..., description="Password of the user", pattern=r"^[0-9a-zA-Z]") 
    @model_validator(mode="before")
    def email_or_phone(self):
        if not self.user_name and not self.email:
            raise ValueError("Provide either email or phone number")
        return self 
    def email_and_phone(self):
        if self.user_name and self.email:
            raise ValueError("Please input either username of email")
        return self 

# class Forgot_Password()

class User_Create(User_Login):
    name: str = Field(...,description="Name of the user",min_length=2,max_length=100)
    phone: str  = Field(description="Phone number of the user")

    @model_validator(mode="before")
    def validate_phoneno(self):
        if self.phone[0] != "+":
            raise ValueError("Country code should be included in the phone number")
        if self.phone[3:] != 10:
            raise ValueError("Phone number should be atleast 10 digits long") 
    



