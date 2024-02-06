import json
from datetime import datetime

import asyncio

from app.api.db import sessionmanager, User
from app.api.endpoints.users import hash_pass


async def load_users(filename: str) -> None:
        """Наполнение БД тестовыми юзерами."""

        with open(filename, 'r', encoding='utf-8') as file:
            users = json.load(file)
            for user in users:
                async with sessionmanager.session() as session:
                    create_user = User(
                        username=user['username'],
                        password=hash_pass(user['password']),
                        email=user['email'],
                        role=user['role'],
                    )
                    session.add(create_user)
                    await session.commit()
        print(f'БД заполнена тестовыми user-ами')


async def main():
    await load_users('data/test_users.json')


if __name__ == "__main__":
    asyncio.run(main())
