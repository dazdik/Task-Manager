from fastapi import APIRouter
from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from starlette.requests import Request

from app.api.db import Task, User, sessionmanager
from app.api.db.models import UserRole, UserTasksAssociation
from app.api.db.settings_db import settings
from app.api.endpoints.auth import create_access_token, verify_password

router = APIRouter(include_in_schema=False)


class UserModelView(ModelView, model=User):
    column_list = [
        User.id,
        User.username,
        User.email,
        User.role,
        User.created_at,
        User.created_tasks,
        User.user_detail,
    ]
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
        Task.creator_id,
        Task.task_detail,
        Task.creator,
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


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        async with sessionmanager.session() as session:
            form = await request.form()
            username = form["username"]
            password = form["password"]

            stmt = select(User).filter(User.username == username)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if (
                user
                and verify_password(password, user.password)
                and user.role == UserRole.ADMIN
            ):
                request.session.update(
                    {
                        "token": create_access_token(
                            data={"user_id": user.id, "token_type": "Bearer"}
                        )
                    }
                )
                return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
        return True


@router.post("/login")
async def login(request: Request):
    auth_backend = AdminAuth(settings.AUTH.KEY)
    await auth_backend.login(request)
