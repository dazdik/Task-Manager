from datetime import datetime, date
from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy import Date

from app.api.db import TaskStatus, Task


class TaskFilter(Filter):
    name__ilike: str | None = None
    status: TaskStatus | None = None
    created_at: date | None = None

    class Constants(Filter.Constants):
        model = Task
