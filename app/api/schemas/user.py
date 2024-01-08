from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.api.db import UserRole


class UserBaseSchema(BaseModel):
    username: str
    email: EmailStr
    created_at: datetime


class CreateUserSchema(UserBaseSchema):
    hashed_password: str = Field(alias="password")
    role: UserRole = UserRole.USER


class UserSchema(UserBaseSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class DataToken(BaseModel):
    id: int | None = None
