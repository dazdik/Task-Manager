from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.api.db import TaskStatus


class CreateTaskSchema(BaseModel):
    name: str = Field(max_length=155)
    description: str | None = None
    created_at: datetime
    urgency: bool = False
    executors_id: list[int]


class SuccessResponse(BaseModel):
    status: str
    message: str


class TaskUpdatePartial(BaseModel):
    description: str | None = None
    urgency: bool | None = None
    status: TaskStatus | None = None
    executors_id: list[int] | None = None


class UserBase(BaseModel):
    id: int
    username: str
    email: str


class TaskExecutor(UserBase):
    pass


class TaskCreator(UserBase):
    pass


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    created_at: datetime
    urgency: bool
    status: TaskStatus
    creator: TaskCreator
    executors: list[TaskExecutor]


class TaskInWork(BaseModel):
    id: int
    name: str


class TaskUserResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    urgency: bool
    status: TaskStatus



