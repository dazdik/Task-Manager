from fastapi import APIRouter, Depends, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload, aliased

from app.api.db import UserRole, get_db_session, Task
from app.api.db.models import UserTasksAssociation, User
from app.api.endpoints.dependencies import check_role
from app.api.schemas import CreateTaskSchema, SuccessResponse
from app.api.endpoints.dependencies import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post(
    "/create", status_code=status.HTTP_201_CREATED, response_model=SuccessResponse
)
@check_role(UserRole.MANAGER)
async def create_task(
    task_data: CreateTaskSchema,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    new_task = Task(
        name=task_data.name,
        description=task_data.description,
        urgency=task_data.urgency,
        creator_id=user.id,
    )

    session.add(new_task)
    await session.flush()  # Flush, чтобы получить new_task.id

    list_user_tasks = [
        UserTasksAssociation(user_id=user_id, task_id=new_task.id)
        for user_id in task_data.executors_id
    ]

    session.add_all(list_user_tasks)
    await session.commit()
    return {
        "status": new_task.status,
        "message": f"Task {new_task.name} successfully created",
    }


@router.get("/{task_id}")
async def get_task_by_id(task_id: int, session: AsyncSession = Depends(get_db_session)):
    # Создаем псевдонимы для разных присоединений таблицы User
    creator = aliased(User, name="creator")
    executor = aliased(User, name="executor")

    stmt = (
        select(
            Task.id,
            Task.name,
            Task.description,
            Task.created_at,
            Task.urgency,
            Task.status,
            Task.creator_id,
            UserTasksAssociation.user_id.label("executor_id"),
            creator.username.label("creator_username"),
            executor.username.label("executor_username"),
        )
        .join(UserTasksAssociation, UserTasksAssociation.task_id == Task.id)
        .join(creator, Task.creator_id == creator.id)
        .join(executor, UserTasksAssociation.user_id == executor.id)
        .where(Task.id == task_id)
    )
    result = await session.execute(stmt)
    task = result.fetchone()

    if not task:
        return None

    task_data = {
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "created_at": task.created_at,
        "urgency": task.urgency,
        "status": task.status,
        "creator_id": task.creator_id,
        "creator_username": task.creator_username,
        "executor_id": task.executor_id,
        "executor_username": task.executor_username,
    }

    return task_data
    # # stmt = (
    # #     select(Task)
    # #     .options(selectinload(Task.task_detail).joinedload(UserTasksAssociation.user))
    # #     .where(Task.id == task_id)
    # # )
    # # res = await session.execute(stmt)
    # # task = res.scalar_one_or_none()
    # # return task

