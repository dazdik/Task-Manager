import asyncio
import json
import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.db import Task, User, UserRole, sessionmanager
from app.api.db.models import UserTasksAssociation
from app.api.endpoints.users import hash_pass


async def filter_user_role(role: UserRole, session: AsyncSession):
    stmt = await session.execute(select(User).where(User.role == role))
    return stmt


async def load_users(filename: str) -> None:
    """Наполнение БД тестовыми юзерами."""

    with open(filename, "r", encoding="utf-8") as file:
        users = json.load(file)
        for user in users:
            async with sessionmanager.session() as session:
                new_user = User(
                    username=user["username"],
                    password=hash_pass(user["password"]),
                    email=user["email"],
                    role=user["role"],
                )
                session.add(new_user)
                await session.commit()
    print(f"БД заполнена тестовыми user-ами")


async def load_tasks(filename: str) -> None:
    with open(filename, "r", encoding="utf-8") as file:
        tasks = json.load(file)
        data_executors = []
        data_creators = []
        async with sessionmanager.session() as session:
            stmt = await filter_user_role(role=UserRole.USER, session=session)
            data_executors.extend([executor.id for executor in stmt.scalars().all()])
            stmt = await filter_user_role(role=UserRole.MANAGER, session=session)
            data_creators.extend([creator.id for creator in stmt.scalars().all()])
            for task in tasks:
                new_task = Task(
                    name=task["name"],
                    description=task["description"],
                    creator_id=random.choice(data_creators),
                )
                session.add(new_task)
                await session.flush()
                list_users_task = [
                    UserTasksAssociation(
                        user_id=random.choice(data_executors), task_id=new_task.id
                    )
                ]
                session.add_all(list_users_task)
            await session.commit()

    print(f"Таски успешно добавлены")


async def main():
    await load_users("data/test_users.json")
    await load_tasks("data/test_tasks.json")


if __name__ == "__main__":
    asyncio.run(main())
