from datetime import date

from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy.orm import aliased

from app.api.db import Task, TaskStatus, User
from app.api.db.models import UserRole, UserTasksAssociation


class UserTaskFilter(Filter):
    username: str | None = None

    class Constants(Filter.Constants):
        model = aliased(User, name="creators2")


class ExecutorFilter(Filter):
    username: str | None = None

    class Constants(Filter.Constants):
        model = User


class TaskFilter(Filter):
    name__ilike: str | None = None
    status: TaskStatus | None = None
    created_at: date | None = None
    deadline: date | None = None
    creator: UserTaskFilter | None = FilterDepends(
        with_prefix("creator", UserTaskFilter)
    )

    executor: ExecutorFilter | None = FilterDepends(
        with_prefix("executor", ExecutorFilter)
    )
    order_by: list[str] | None = None

    class Constants(Filter.Constants):
        model = Task

    def apply_users_filter(self, query):
        uta_alias = aliased(UserTasksAssociation)
        executor_alias = aliased(User, name="executor_alias")
        if self.creator and self.creator.username:
            query = query.where(
                Task.creator.has(User.username == self.creator.username)
            )

        if self.executor and self.executor.username:
            query = (
                query.join(uta_alias, Task.id == uta_alias.task_id)
                .join(executor_alias, uta_alias.user_id == executor_alias.id)
                .where(executor_alias.username == self.executor.username)
            )

        return query


class UserFilter(UserTaskFilter):
    email__ilike: str | None = None
    role: UserRole | None = None
    order_by: list[str] | None = None
