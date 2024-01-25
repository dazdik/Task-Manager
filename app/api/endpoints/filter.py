from datetime import date

from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter

from app.api.db import TaskStatus, Task, UserRole, User
from app.api.db.models import UserTasksAssociation


class UserFilter(Filter):
    username: str | None = None
    role: UserRole | None = None

    class Constants(Filter.Constants):
        model = User


class ExecutorFilter(Filter):
    user: UserFilter | None = FilterDepends(with_prefix("user", UserFilter))

    class Constants(Filter.Constants):
        model = UserTasksAssociation


class TaskFilter(Filter):
    name__ilike: str | None = None
    status: TaskStatus | None = None
    created_at: date | None = None
    creator: UserFilter | None = FilterDepends(with_prefix("creator", UserFilter))
    executor__user__username: ExecutorFilter | None = FilterDepends(
        with_prefix("executor", ExecutorFilter)
    )

    class Constants(Filter.Constants):
        model = Task
