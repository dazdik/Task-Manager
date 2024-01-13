from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, status
from sqladmin import Admin

from app.api import router
from app.api.db import User, UserRole, sessionmanager
from app.api.db.admin import (AdminAuth, TaskModelView, UserModelView,
                              UserTasksAssociationModelView)
from app.api.db.admin import router as admin_router
from app.api.db.settings_db import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    if sessionmanager.engine is not None:
        await sessionmanager.close()


app = FastAPI(lifespan=lifespan)


admin = Admin(
    app=app,
    session_maker=sessionmanager.session_maker,
    authentication_backend=AdminAuth(settings.AUTH.KEY),
)
admin.add_view(UserModelView)
admin.add_view(TaskModelView)
admin.add_view(UserTasksAssociationModelView)
app.include_router(router)
app.include_router(admin_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8066,
        reload=True,
        workers=3,
    )
