from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.db import Task
from app.api.db.models import UserTasksAssociation
from app.api.schemas import TaskCreator, TaskExecutor, TaskResponse


async def get_task_by_id(task_id: int, session: AsyncSession):
    result = await session.execute(
        select(Task)
        .options(
            joinedload(Task.creator),
            joinedload(Task.task_detail).joinedload(UserTasksAssociation.user),
        )
        .where(Task.id == task_id)
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="This task not found"
        )
    return task


async def get_task_response(task):
    task_data = TaskResponse(
        id=task.id,
        name=task.name,
        description=task.description,
        created_at=task.created_at,
        deadline=task.deadline,
        urgency=task.urgency,
        status=task.status,
        creator=TaskCreator(
            id=task.creator.id,
            username=task.creator.username,
            email=task.creator.email,
        )
        if task.creator
        else "Creator will be add soon",
        executors=[
            TaskExecutor(
                id=executor.user.id,
                username=executor.user.username,
                email=executor.user.email,
            )
            for executor in task.task_detail
        ],
    )
    return task_data
