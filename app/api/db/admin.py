from fastapi import Depends, APIRouter, HTTPException
from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.requests import Request

from app.api.db import User, Task, get_db_session, sessionmanager
from app.api.db.models import UserTasksAssociation, UserRole
from app.api.db.settings_db import settings
from app.api.endpoints.auth import create_access_token, verify_password


router = APIRouter(include_in_schema=False)


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


async def check_user(
    username: str,
    password: str,
    session: AsyncSession = Depends(get_db_session),
):
    stmt = select(User).filter(username == User.username)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    # print(user)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]

        user = await check_user(username=username, password=password)
        if user and user.role == UserRole.ADMIN:
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
        print(token)
        if not token:
            return False
        return True


@router.post("/login")
async def login(request: Request):
    if await AdminAuth.login(settings.AUTH.KEY, request):
        return {"message": "Successfully logged in."}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password."
    )
