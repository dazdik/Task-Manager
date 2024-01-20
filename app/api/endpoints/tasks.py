from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    status,
    WebSocket,
    WebSocketException,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.websockets import WebSocketState, WebSocketDisconnect


from app.api.db import Task, UserRole, get_db_session
from app.api.db.models import User, UserTasksAssociation
from app.api.endpoints.dependencies import (
    check_role,
    check_role_for_status,
    get_current_user,
    get_task_by_id,
    send_email_async,
)
from app.api.schemas import (
    CreateTaskSchema,
    SuccessResponse,
    TaskCreator,
    TaskExecutor,
    TaskResponse,
    TaskUpdatePartial,
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


class WebSocketManager:
    def __init__(self):
        self.active_websockets: dict[int, list[WebSocket]] = {}

    async def connect(self, task_id: int, websocket: WebSocket):
        await websocket.accept()
        if task_id not in self.active_websockets:
            self.active_websockets[task_id] = []
        self.active_websockets[task_id].append(websocket)

    async def disconnect(self, task_id: int, websocket: WebSocket):
        self.active_websockets.get(task_id).remove(websocket)

    async def send_message(self, task_id: int, message: dict):
        clients = self.active_websockets.get(task_id, [])
        for ws in clients:  # type: WebSocket
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_json(message)
            except Exception as e:
                print(f"Error sending message: {e}")


ws_manager = WebSocketManager()


@router.websocket("/ws/{task_id}")
async def websocket_endpoint(
    websocket: WebSocket, task_id: int, session=Depends(get_db_session)
):
    task = await get_task_by_id(task_id, session)
    if not task:
        raise WebSocketException(
            code=status.HTTP_404_NOT_FOUND, reason="this task does not exist"
        )
    token = websocket.headers.get("authorization").split("Bearer ")[1]
    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    user = await get_current_user(token, session)
    if not user:
        raise WebSocketException(code=status.HTTP_401_UNAUTHORIZED)
    executors_id = [executor.user_id for executor in task.task_detail]
    if user.id == task.creator.id or user.id in executors_id:
        await ws_manager.connect(task_id, websocket)
        try:
            while True:
                data = await websocket.receive_text()

                await ws_manager.send_message(task.id, message={"message": "hi"})

        except WebSocketDisconnect as e:
            await ws_manager.disconnect(task_id, websocket)
            print(f"Error: {e}")
        finally:
            await websocket.close()
    else:
        print("aaaaaaaa помогите")


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
    # await broadcast_message(f"New task {new_task.name} created by {user.username}")
    return {
        "status": new_task.status,
        "message": f"Task {new_task.name} successfully created",
    }


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_id(task_id: int, session: AsyncSession = Depends(get_db_session)):
    """Получение таски по айди с информацией о создателе задачи и исполнителе/исполнителях."""

    task = await get_task_by_id(task_id, session)
    task_data = TaskResponse(
        id=task.id,
        name=task.name,
        description=task.description,
        created_at=task.created_at,
        urgency=task.urgency,
        status=task.status,
        creator=TaskCreator(
            id=task.creator.id, username=task.creator.username, email=task.creator.email
        ),
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
            task_id, message=SuccessResponse(status="aaa", message="bbbb").model_dump()
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
    await ws_manager.send_message(task.id, message={"message": "hi"})

    return {"massage": f"User {user.username} update the task"}
