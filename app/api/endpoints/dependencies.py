from email.message import EmailMessage
from functools import wraps

import aiosmtplib
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.db import TaskStatus, User, UserRole, get_db_session
from app.api.endpoints.auth import verify_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login/")


async def get_current_user(
    token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db_session)
):
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
    status_for_user = {
        UserRole.USER: [TaskStatus.AT_WORK, TaskStatus.ON_CHECK],
        UserRole.MANAGER: [TaskStatus.FROZEN, TaskStatus.CANCEL, TaskStatus.FINISHED],
    }
    return status_for_user[user.role]


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
        username="alberv0r@yandex.ru",
        password="hnimqbfsiartqzqk",
        use_tls=True
    )


# async def send_notification(background_tasks: BackgroundTasks, user_email: str):
#     background_tasks.add_task(
#         send_email_async,
#         "Привет",
#         "Текст письма",
#         user_email
#     )
#     return {"message": "Notification will be sent in the background"}
