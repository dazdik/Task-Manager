from fastapi import APIRouter, Depends, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.db import UserRole, get_db_session, Task
from app.api.db.models import UserTasksAssociation
from app.api.endpoints.dependencies import check_role
from app.api.schemas import TaskSchema
from app.api.endpoints.dependencies import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/create", status_code=status.HTTP_201_CREATED, response_model=TaskSchema)
@check_role(UserRole.MANAGER)
async def create_task(
    task_data: TaskSchema,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    new_task = Task(
        name=task_data.name,
        description=task_data.description,
        urgency=task_data.urgency,
        status=task_data.status,
        task_detail=UserTasksAssociation(user_id=user.id, task_id=Task.id),
    )
    session.add(new_task)
    await session.commit()
    await session.refresh(new_task)
