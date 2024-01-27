from datetime import date

from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import EmailStr
from sqlalchemy.orm import aliased

from app.api.db import Task, TaskStatus, User
from app.api.db.models import UserTasksAssociation, UserRole


class UserTaskFilter(Filter):
    username: str | None = None

    class Constants(Filter.Constants):
        model = User


class ExecutorFilter(Filter):
    user: UserTaskFilter | None = FilterDepends(with_prefix("executor", UserTaskFilter))

    class Constants(Filter.Constants):
        model = UserTasksAssociation


class TaskFilter(Filter):
    name__ilike: str | None = None
    status: TaskStatus | None = None
    created_at: date | None = None
    executor: ExecutorFilter | None = FilterDepends(
        with_prefix("executor", ExecutorFilter)
    )
    order_by: list[str] | None = None

    class Constants(Filter.Constants):
        model = Task

    def apply_users_filter(self, query):
        executor_alias = aliased(User, name="executor_alias")
        uta_alias = aliased(UserTasksAssociation, name="uta_alias")

        if self.executor and self.executor.user and self.executor.user.username:
            query = (
                query.join(uta_alias, Task.id == uta_alias.task_id)
                .join(executor_alias, uta_alias.user_id == executor_alias.id)
                .where(executor_alias.username == self.executor.user.username)
            )

        return query


class UserFilter(UserTaskFilter):
    email__ilike: str | None = None
    role: UserRole | None = None
    order_by:  list[str] | None = None


