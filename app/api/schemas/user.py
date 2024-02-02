import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.api.db import UserRole
from app.api.schemas import TaskInWork, TaskUserResponse


class UserBaseSchema(BaseModel):
    username: str
    email: EmailStr
    created_at: datetime


class CreateUserSchema(UserBaseSchema):
    password: str
    role: UserRole = UserRole.USER

    @field_validator("role")
    def check_role(cls, v):
        if v in (UserRole.MANAGER, UserRole.ADMIN):
            raise ValueError("You can't assign yourself such a role.")

    @field_validator("password")
    def check_pass(cls, v):
        regex = r"(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}"

        if not re.fullmatch(regex, v):
            raise ValueError(
                f"the password must contain more than 8 characters"
                f"and contain Latin letters of different case and numbers"
            )
        return v

    @field_validator("username")
    def username_alphanumeric(cls, v):
        assert v.isalnum()
        assert v.istitle()
        return v


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


class UserUpdatePartial(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    role: UserRole | None = None


class UsersAllSchemas(UserBaseSchema):
    role: UserRole
    id: int
