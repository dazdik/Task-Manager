from datetime import datetime, timedelta, date

from fastapi import HTTPException, status
from fastapi_filter.contrib.sqlalchemy import Filter


from app.api.db import TaskStatus, Task


class TaskFilter(Filter):
    name__ilike: str | None = None
    description__ilike: str | None = None
    status: TaskStatus | None = None
    created_at: date | None = None

    class Constants(Filter.Constants):
        model = Task
