from pydantic import BaseModel, Field


class CreateTaskEvent(BaseModel):
    event: str = Field(default="create_task")
    name: str
    description: str
    urgency: int
    executors_id: list[int]
