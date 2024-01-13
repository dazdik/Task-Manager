from fastapi import APIRouter, Depends, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.db import UserRole, get_db_session, Task
from app.api.db.models import UserTasksAssociation
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