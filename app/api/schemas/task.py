from datetime import date

from pydantic import (BaseModel, ConfigDict, Field, field_serializer,
                      field_validator)

from app.api.db import TaskStatus


def normalize(name: str) -> str:
    return name.capitalize()


class CreateTaskSchema(BaseModel):
    name: str = Field(max_length=155)
    description: str | None = None
    created_at: date
    deadline: date
    urgency: bool = False
    executors_id: list[int]

    normalize_name = field_validator("name")(normalize)
    normalize_description = field_validator("description")(normalize)


class SuccessResponse(BaseModel):
    status: str
    message: str


class TaskUpdatePartial(BaseModel):
    description: str | None = None
    urgency: bool | None = None
    status: TaskStatus | None = None
    executors_id: list[int] | None = None


class UserBase(BaseModel):
    id: int | None
    username: str | None
    email: str | None


class TaskExecutor(UserBase):
    pass


class TaskCreator(UserBase):
    pass


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    created_at: date
    deadline: date | None = None
    urgency: bool
    status: TaskStatus
    creator: TaskCreator | str
    executors: list[TaskExecutor]


class TaskInWork(BaseModel):
    id: int
    name: str


class TaskUserResponse(BaseModel):
    id: int
    name: str
    created_at: date
    deadline: date
    urgency: bool
    status: TaskStatus
