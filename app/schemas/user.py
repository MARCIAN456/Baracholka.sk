import uuid
from inspect import classify_class_attrs

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, EmailStr



class UserCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=5,
        max_length=30
    )
    email: EmailStr = Field(
        ...,
        max_length=255,
        description="Електронна адресса"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Minimum 8 letters"
    )
    city: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Місто проживання (обов'язково)"
    )
    country: str = Field(
        "Slovakia",
        min_length=2,
        max_length=50,
        description="Країна проживання"
    )
class UserLogin(BaseModel):
    email: EmailStr = Field(
        ...,
        max_length=255,
        description="Електронна адресса"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Minimum 8 letters"
    )

class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr
    city: str
    country: str

    model_config = ConfigDict(from_attributes=True)





