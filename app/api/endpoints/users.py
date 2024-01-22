from fastapi import APIRouter, Depends, status, HTTPException
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.db import User, UserRole, get_db_session
from app.api.db.models import UserTasksAssociation
from app.api.endpoints.dependencies import check_role, get_current_user
from app.api.schemas import (
    CreateUserSchema,
    TaskInWork,
    TaskUserResponse,
    UserResponse,
    UserUpdatePartial,
)

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
    return user_data


@router.delete("/{user_id}")
@check_role(UserRole.ADMIN)
async def user_delete(
    user_id: int,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    stmt = await session.execute(select(User).where(User.id == user_id))
    user_del = stmt.scalar_one_or_none()
    await session.delete(user_del)
    await session.commit()
    return {"message": f"{user_del.username} successfully deleted"}


@router.patch("{user_id}")
async def change_user(
    user_id: int,
    user_in: UserUpdatePartial,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    stmt = await session.execute(select(User).where(User.id == user_id))
    user_update = stmt.scalar_one_or_none()
    if not user_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not (user.role == UserRole.ADMIN or user.id == user_update.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges"
        )
    for name, value in user_in.model_dump(exclude_unset=True).items():
        if name == "role":
            if user.id == user_update.id or user.role != UserRole.ADMIN:
                raise HTTPException(status_code=403, detail="Cannot change role")
            else:
                user_update.role = value
                continue
        if name == "password":
            value = hash_pass(value)

        setattr(user_update, name, value)
    await session.commit()
    return "user update"
