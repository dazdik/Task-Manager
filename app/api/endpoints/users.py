from fastapi import APIRouter, Depends, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.db import User, UserRole, get_db_session
from app.api.db.models import UserTasksAssociation
from app.api.endpoints.dependencies import check_role, get_current_user
from app.api.schemas import (CreateUserSchema, TaskInWork, TaskUserResponse,
                             UserResponse)

router = APIRouter(prefix="/users", tags=["Users"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_pass(password: str):
    return pwd_context.hash(password)


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: CreateUserSchema, session: AsyncSession = Depends(get_db_session)
):
    """Создание аккаунта юзера."""

    hashed_pass = hash_pass(user_in.hashed_password)

    user = User(
        email=user_in.email,
        password=hashed_pass,
        username=user_in.username,
        role=user_in.role,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.get("/all")
async def get_users(session: AsyncSession = Depends(get_db_session)):
    """Получение списка всех юзеров с краткой информацией."""

    stmt = await session.execute(select(User).order_by(User.id))
    users = stmt.scalars().all()
    users_without_passwords = []

    for user in users:
        user_data = {
            column.name: getattr(user, column.name)
            for column in user.__table__.columns
            if column.name != "password"
        }
        users_without_passwords.append(user_data)

    return users_without_passwords


@router.get("/me")
@check_role(UserRole.ADMIN, UserRole.MANAGER, UserRole.USER)
async def get_me(user: User = Depends(get_current_user)):
    return user.username


@router.get("/{user_id}")
async def get_user_by_id(user_id: int, session: AsyncSession = Depends(get_db_session)):
    """Получение информации о юзере с тасками, в которых он является исполнителем или создателем."""

    res = await session.execute(
        select(User)
        .options(
            joinedload(User.created_tasks),
            joinedload(User.user_detail).joinedload(UserTasksAssociation.task),
        )
        .where(User.id == user_id)
    )
    user = res.scalars().first()
    user_data = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        created_at=user.created_at,
        role=user.role,
        created_tasks=[
            TaskUserResponse(
                id=task.id,
                name=task.name,
                created_at=task.created_at,
                urgency=task.urgency,
                status=task.status,
            )
            for task in user.created_tasks
        ],
        in_work=[
            TaskInWork(id=assoc.task.id, name=assoc.task.name)
            for assoc in user.user_detail
        ],
    )

    #
    # user_data = {
    #     "id": user.id,
    #     "username": user.username,
    #     "email": user.email,
    #     "created_at": user.created_at,
    #     "role": user.role,
    #     "created_tasks": [
    #         {
    #             "id": task.id,
    #             "name": task.name,
    #             "created_at": task.created_at,
    #             "urgency": task.urgency,
    #             "status": task.status,
    #         }
    #         for task in user.created_tasks
    #     ],
    #     "in work": [
    #         {"id": assoc.task.id, "name": assoc.task.name} for assoc in user.user_detail
    #     ],
    # }
    return user_data
