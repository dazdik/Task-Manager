from pydantic import BaseModel, Field
from datetime import datetime

from app.api.db import TaskStatus


class CreateTaskSchema(BaseModel):
    name: str = Field(max_length=155)
    description: str | None = None
    created_at: datetime
    urgency: bool = False
    executors_id: list[int]


<<<<<<< HEAD
class CreateTaskSchema(BaseModel):
    name: str = Field(max_length=155)
    description: str | None = None
    created_at: datetime
    urgency: bool = False
    status: TaskStatus = TaskStatus.CREATED

class GetUserTaskSchema(BaseModel):
    user_id: int
    tasks: List[TaskSchema]
=======
class SuccessResponse(BaseModel):
    status: str
    message: str
>>>>>>> b26d71b0c41e3503a72aec17045ee5481871ce3c
