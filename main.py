from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.db import sessionmanager
from sqladmin import Admin

from app.api.db.admin import UserModelView, TaskModelView, UserTasksAssociationModelView
from app.api.endpoints.users import router as user_routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    if sessionmanager.engine is not None:
        await sessionmanager.close()


app = FastAPI(lifespan=lifespan)
admin = Admin(app=app, session_maker=sessionmanager.session_maker)
admin.add_view(UserModelView)
admin.add_view(TaskModelView)
admin.add_view(UserTasksAssociationModelView)
app.include_router(user_routers)
