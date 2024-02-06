import asyncio

from sqlalchemy import select

from app.api.db import User, UserRole, sessionmanager
from app.api.endpoints.users import hash_pass


async def create_superuser(username: str, password: str, email: str):
    """Создание суперпользователя."""

    async with sessionmanager.session() as session:
        stmt = select(User).filter(
            (User.username == username)
            | (User.email == email)
            | (User.role == UserRole.ADMIN)
        )
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            print("Superuser already exists!")
            return False

        if user is None:
            hashed_password = hash_pass(password)
            superuser = User(
                username=username,
                password=hashed_password,
                email=email,
                role=UserRole.ADMIN,
            )
            session.add(superuser)
            await session.commit()

        return True


async def main():
    username = input("Введите имя пользователя: ")
    password = input("Введите пароль: ")
    email = input("Введите email: ")
    await create_superuser(username, password, email)


if __name__ == "__main__":
    asyncio.run(main())
