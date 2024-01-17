from datetime import datetime

from pydantic import BaseModel, Field

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
