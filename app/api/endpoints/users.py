from fastapi import APIRouter, Depends, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.db import User, UserRole, get_db_session
from app.api.endpoints.dependencies import check_role, get_current_user
from app.api.schemas import CreateUserSchema

router = APIRouter(prefix="/users", tags=["Users"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_pass(password: str):
    return pwd_context.hash(password)


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: CreateUserSchema, session: AsyncSession = Depends(get_db_session)
):
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
