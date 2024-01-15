from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.db import Task, UserRole, get_db_session
from app.api.db.models import TaskStatus, User, UserTasksAssociation
from app.api.endpoints.dependencies import check_role, check_status, get_current_user
from app.api.schemas import CreateTaskSchema, SuccessResponse

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
    await session.flush()

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
    result = await session.execute(
        select(Task)
        .options(
            joinedload(Task.creator),
            joinedload(Task.task_detail).joinedload(UserTasksAssociation.user),
        )
        .where(Task.id == task_id)
    )
    task = result.scalars().first()
    task_data = {
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "created_at": task.created_at,
        "urgency": task.urgency,
        "status": task.status,
        "creator": {
            "id": task.creator.id,
            "username": task.creator.username,
            "email": task.creator.email,
        },
        "executors": [
            {
                "id": assoc.user.id,
                "username": assoc.user.username,
                "email": assoc.user.email,
            }
            for assoc in task.task_detail
        ],
    }
    return task_data


@router.delete("/{task_id}")
@check_role(UserRole.MANAGER)
async def delete_task_id(
    task_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(
        select(Task).where(Task.id == task_id, Task.creator_id == user.id)
    )
    task = result.scalar_one_or_none()
    if task:
        await session.delete(task)
        await session.commit()
        return {"massage": f"{user.username} successfully deleted the task {task}"}
    return {"massage": f"This task does not exist or you do not have permissions"}


@router.patch("/{task_id}")
@check_status(TaskStatus.CREATED)
@check_role(UserRole.USER)
async def update_task(
    task_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    res = await session.execute(
        select(User)
        .options(
            joinedload(User.user_detail).joinedload(UserTasksAssociation.task),
        )
        .where(User.id == user.id)
    )
    executor = res.scalars().first()
    tasks = [i.task_id for i in executor.user_detail]
    if task_id in tasks:
        stmt = await session.execute(select(Task).where(Task.id == task_id))
        res = stmt.scalar_one_or_none()
        res.status = TaskStatus.AT_WORK
        session.add(res)
        await session.commit()
        return {"massage": f"Slave {user.username} accepted the task"}
