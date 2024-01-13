from typing import List

from pydantic import BaseModel, Field
from datetime import datetime

from app.api.db import TaskStatus


class TaskSchema(BaseModel):
    name: str = Field(max_length=155)
    description: str | None = None
    created_at: datetime
    urgency: bool = False
    status: TaskStatus = TaskStatus.CREATED
    task_detail: list


class GetUserTaskSchema(BaseModel):
    user_id: int
    tasks: List[TaskSchema]
