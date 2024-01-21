from email.message import EmailMessage
from functools import wraps

import aiosmtplib
from fastapi import Depends, HTTPException, status, WebSocket, WebSocketException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.db import Task, TaskStatus, User, UserRole, get_db_session
from app.api.db.models import UserTasksAssociation
from app.api.db.settings_db import settings
from app.api.endpoints.auth import verify_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login/")


async def get_current_user(
    token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db_session)
):
    """Получение текущего юзера."""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Failed to verify credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = verify_access_token(
        token=token, credentials_exception=credentials_exception
    )
    stmt = select(User).where(token.id == User.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    return user


def check_role(*roles):
    """Декоратор для проверки роли пользователя."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user: User = kwargs.get("user")
            if user.role not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="The user doesn't have enough privileges",
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


async def check_role_for_status(user: User):
    """Проверка доступных статусов для юзеров и менеджеров."""

    status_for_user = {
        UserRole.USER: [TaskStatus.AT_WORK, TaskStatus.ON_CHECK],
        UserRole.MANAGER: [TaskStatus.FROZEN, TaskStatus.CANCEL, TaskStatus.FINISHED],
    }
    return status_for_user[user.role]


async def get_task_by_id(task_id: int, session: AsyncSession):
    result = await session.execute(
        select(Task)
        .options(
            joinedload(Task.creator),
            joinedload(Task.task_detail).joinedload(UserTasksAssociation.user),
        )
        .where(Task.id == task_id)
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="This task not found"
        )
    return task


async def send_email_async(subject: str, body: str, to_email: str):
    message = EmailMessage()
    message["From"] = "alberv0r@yandex.ru"
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    await aiosmtplib.send(
        message,
        hostname="smtp.yandex.ru",
        port=465,
        username=settings.EMAIL.NAME,
        password=settings.EMAIL.PASS,
        use_tls=True,
    )


async def get_user_with_token(websocket: WebSocket, session: AsyncSession):
    token = websocket.headers.get("authorization").split("Bearer ")[1]
    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    user = await get_current_user(token, session)
    if not user:
        raise WebSocketException(code=status.HTTP_401_UNAUTHORIZED)
    return user
