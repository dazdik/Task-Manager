import argparse
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
            print("superuser already exists")
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
    parser = argparse.ArgumentParser(description="Создание суперпользователя.")
    parser.add_argument("--username", required=True, help="Имя пользователя")
    parser.add_argument("--email", required=True, help="Email пользователя")
    parser.add_argument("--password", required=True, help="Пароль пользователя")
    args = parser.parse_args()

    await create_superuser(
        username=args.username, password=args.password, email=args.email
    )


if __name__ == "__main__":
    asyncio.run(main())
