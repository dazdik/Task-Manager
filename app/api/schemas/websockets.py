from pydantic import BaseModel, Field


class TaskEvent(BaseModel):
    event: str = Field(default="create_task")
    message: str
