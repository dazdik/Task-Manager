from sqladmin import ModelView

from app.api.db import User, Task


# from main import admin
from app.api.db.models import UserTasksAssociation


class UserModelView(ModelView, model=User):
    column_list = [User.id, User.username, User.email, User.role, User.created_at]
    column_sortable_list = [User.id]
    column_searchable_list = [User.username, User.role]


class TaskModelView(ModelView, model=Task):
    column_list = [
        Task.id,
        Task.name,
        Task.description,
        Task.created_at,
        Task.status,
        Task.urgency,
    ]
    column_sortable_list = [Task.id, Task.created_at]
    column_searchable_list = [Task.name]


class UserTasksAssociationModelView(ModelView, model=UserTasksAssociation):
    column_list = [
        UserTasksAssociation.user,
        UserTasksAssociation.user_id,
        UserTasksAssociation.task,
        UserTasksAssociation.task_id,
    ]
