from datetime import date

from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy.orm import aliased

from app.api.db import TaskStatus, Task, UserRole, User
from app.api.db.models import UserTasksAssociation


class UserTaskFilter(Filter):
    username: str | None = None

    class Constants(Filter.Constants):
        model = User


class ExecutorFilter(Filter):
    user: UserTaskFilter | None = FilterDepends(with_prefix("user", UserTaskFilter))

    class Constants(Filter.Constants):
        model = UserTasksAssociation


class TaskFilter(Filter):
    name__ilike: str | None = None
    status: TaskStatus | None = None
    created_at: date | None = None
    creator: UserTaskFilter | None = FilterDepends(
        with_prefix("creator", UserTaskFilter)
    )
    executor: ExecutorFilter | None = FilterDepends(
        with_prefix("task_detail", ExecutorFilter)
    )

    class Constants(Filter.Constants):
        model = Task

    def apply_creator_filter(self, query):
        if self.creator and self.creator.username:
            creator_alias = aliased(User)
            query = query.join(
                creator_alias, Task.creator_id == creator_alias.id
            ).where(creator_alias.username == self.creator.username)
        return query

    def apply_executor_filter(self, query):
        if self.executor and self.executor.user and self.executor.user.username:
            username = self.executor.user.username
            user_alias = aliased(User)
            uta_alias = aliased(UserTasksAssociation)
            query = (
                query.join(uta_alias, Task.task_detail)
                .join(user_alias, uta_alias.user)
                .where(user_alias.username == username)
            )
        return query
