from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketException,
    status,
)
from fastapi.websockets import WebSocketDisconnect
from fastapi_cache.decorator import cache
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, paginate
from fastapi_pagination.utils import disable_installed_extensions_check

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, joinedload

from app.api.core import websocket_, ws_manager
from app.api.db import Task, UserRole, get_db_session
from app.api.db.models import User, UserTasksAssociation
from app.api.endpoints.filter import TaskFilter
from app.api.endpoints.tasks_utils import get_task_by_id, get_task_response
from app.api.endpoints.users_utils import (
    check_role,
    check_role_for_status,
    get_current_user,
    get_user_with_token,
    send_email_async,
)
from app.api.schemas import (
    CreateTaskSchema,
    SuccessResponse,
    TaskEvent,
    TaskResponse,
    TaskUpdatePartial,
)

disable_installed_extensions_check()


router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.websocket("/ws/")
async def websocket_endpoint_create_task(
    websocket: WebSocket, session=Depends(get_db_session)
):
    await websocket_(websocket, session)


@router.websocket("/ws/{task_id}")
async def websocket_endpoint(
    websocket: WebSocket, task_id: int, session=Depends(get_db_session)
):
    task = await get_task_by_id(task_id, session)
    if not task:
        raise WebSocketException(
            code=status.HTTP_404_NOT_FOUND, reason="this task does not exist"
        )
    user = await get_user_with_token(websocket, session)
    executors_id = [executor.user_id for executor in task.task_detail]
    if user.id == task.creator.id or user.id in executors_id:
        await ws_manager.connect(task_id, websocket)
        try:
            while True:
                data = await websocket.receive_text()

        except WebSocketDisconnect as e:
            await ws_manager.disconnect(task_id, websocket)
            print(f"Error: {e}")
        finally:
            await websocket.close()


@router.post(
    "/create", status_code=status.HTTP_201_CREATED, response_model=SuccessResponse
)
@check_role(UserRole.MANAGER)
async def create_task(
    task_data: CreateTaskSchema,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Создание таски с исполнителями с ролью юзера."""

    new_task = Task(
        name=task_data.name,
        description=task_data.description,
        urgency=task_data.urgency,
        creator_id=user.id,
        deadline=task_data.deadline,
    )

    session.add(new_task)
    await session.flush()

    list_user_tasks = []
    for user_id in task_data.executors_id:
        stmt = await session.execute(select(User).where(User.id == user_id))
        executor = stmt.scalar_one_or_none()

        if executor.role == UserRole.MANAGER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform the task",
            )
        list_user_tasks.append(
            UserTasksAssociation(user_id=user_id, task_id=new_task.id)
        )

        background_tasks.add_task(
            send_email_async,
            f"Created task {new_task.name}",
            f"{executor.username} you have new task",
            executor.email,
        )

    session.add_all(list_user_tasks)
    await session.commit()
    for executor_id in task_data.executors_id:
        await ws_manager.send_message(
            executor_id,
            message=TaskEvent(message=f"{user.username} create new task").model_dump(),
        )
    return {
        "status": new_task.status,
        "message": f"Task {new_task.name} successfully created",
    }


@router.get("/", response_model=Page[TaskResponse])
@cache(
    expire=60,
)
async def get_all_tasks(
    task_filter: TaskFilter = FilterDepends(TaskFilter),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    query = select(Task).options(
        joinedload(Task.creator),
        joinedload(Task.task_detail).joinedload(UserTasksAssociation.user),
    )

    query = task_filter.filter(query)
    query = task_filter.apply_users_filter(query)
    query = task_filter.sort(query)

    result = await session.execute(query)
    tasks = result.scalars().unique()
    list_of_tasks = []
    for task in tasks:
        task_data = await get_task_response(task)
        list_of_tasks.append(task_data)

    return paginate(list_of_tasks)


@router.get("/{task_id}")
@cache(
    expire=60,
)
async def get_task_id(task_id: int, session: AsyncSession = Depends(get_db_session)):
    """Получение таски по айди с информацией о создателе задачи и исполнителе/исполнителях."""

    task = await get_task_by_id(task_id, session)
    task_data = await get_task_response(task)
    return task_data


@router.delete("/{task_id}")
@check_role(UserRole.MANAGER)
async def delete_task_id(
    task_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Удаление менеджером таски, в которой он является создателем."""
    result = await session.execute(
        select(Task).where(Task.id == task_id, Task.creator_id == user.id)
    )
    task = result.scalar_one_or_none()
    if task:
        await session.delete(task)
        await session.commit()

        await ws_manager.send_message(
            task.id,
            message=TaskEvent(
                event="delete task",
                message=f"Manager {user.username} delete the task #{task.id}",
            ).model_dump(),
        )
        return {"massage": f"{user.username} successfully deleted the task {task}"}
    return {"massage": f"This task does not exist or you do not have permissions"}


@router.patch("/{task_id}")
@check_role(UserRole.USER, UserRole.MANAGER)
async def update_task(
    task_id: int,
    task_data: TaskUpdatePartial,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Обновление таски:
    1. Получение таски и проверка ее на существование
    2. Проверка пользователя, отправившего запрос, на роль и его прав
    3. Юзер может только менять статус, а менеджер может менять все, что пришло в теле запроса
    """
    task = await get_task_by_id(task_id, session)

    if task_data.status not in await check_role_for_status(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This status not allowed",
        )
    executors_id = [executor.user_id for executor in task.task_detail]

    if task_data.executors_id:
        stmt_user = await session.execute(
            select(User).where(User.role == UserRole.USER)
        )
        res = [user.id for user in stmt_user.scalars()]
        for executor_id in task_data.executors_id:
            if executor_id not in res:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

    if user.role == UserRole.USER:
        if (
            task_data.description is not None
            or task_data.urgency is not None
            or task_data.executors_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are only allowed to update the task status",
            )

        task.status = task_data.status

    else:
        for name, value in task_data.model_dump(exclude_unset=True).items():
            if name == "executors_id":
                list_of_new_executors = [
                    UserTasksAssociation(user_id=user_id, task_id=task.id)
                    for user_id in value
                    if user_id not in executors_id
                ]
                session.add_all(list_of_new_executors)
            setattr(task, name, value)

    await session.commit()

    await ws_manager.send_message(
        task.id,
        message=TaskEvent(
            event="update task",
            message=f"{user.username} update the task #{task.id}",
        ).model_dump(),
    )

    return {"massage": f"User {user.username} update the task"}


@router.get("/test")
async def get_test_tasks(
    task_filter: TaskFilter = FilterDepends(TaskFilter),
    session: AsyncSession = Depends(get_db_session),
):
    """Тестовый эндопоинт для фильтрации по полям. С использованием обычных join-ов."""
    creator_alias = aliased(User, name="creators")

    query = (
        select(
            Task,
            creator_alias.id.label("creator_id"),
            creator_alias.username.label("creator_username"),
            creator_alias.email.label("creator_email"),
            func.array_agg(
                func.json_build_object(
                    "id", User.id, "username", User.username, "email", User.email
                )
            ).label("executors"),
        )
        .join(creator_alias, creator_alias.id == Task.creator_id, isouter=True)
        .join(UserTasksAssociation, Task.task_detail, isouter=True)
        .join(User, UserTasksAssociation.user_id == User.id, isouter=True)
        .group_by(Task.id, creator_alias.id)
    )
    query = task_filter.filter(query)
    query = task_filter.apply_users_filter(query)

    query = task_filter.sort(query)
    result = await session.execute(query)
    tasks = result.mappings().all()
    list_of_tasks = []

    for task in tasks:
        key_task = task["Task"]
        list_of_tasks.append(
            {
                "id": key_task.id,
                "name": key_task.name,
                "description": key_task.description,
                "created_at": key_task.created_at,
                "deadline": key_task.deadline,
                "urgency": key_task.urgency,
                "status": key_task.status,
                "creator": {
                    "id": task["creator_id"],
                    "username": task["creator_username"],
                    "email": task["creator_email"]
                    if task["creator_id"]
                    else "Creator will be added soon",
                },
                "executors": task["executors"],
            }
        )
    return list_of_tasks
