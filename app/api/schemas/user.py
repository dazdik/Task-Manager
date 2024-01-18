from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.api.db import UserRole
from app.api.schemas import TaskInWork, TaskUserResponse


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


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    created_at: datetime
    role: UserRole
    created_tasks: list[TaskUserResponse]
    in_work: list[TaskInWork]
