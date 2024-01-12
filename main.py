from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Request, HTTPException, status, Depends

from app.api import router
from app.api.db import sessionmanager, UserRole, User
from sqladmin import Admin

from app.api.db.admin import (
    UserModelView,
    TaskModelView,
    UserTasksAssociationModelView, AdminAuth,
)
from app.api.db.settings_db import settings


from app.api.db.admin import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    if sessionmanager.engine is not None:
        await sessionmanager.close()


app = FastAPI(lifespan=lifespan)


# @app.middleware("http")
# async def auth_middleware(
#     request: Request, call_next, user: User = Depends(get_current_user)
# ):
#     if request.url.path.startswith("/admin"):
#         if not user and user.role != UserRole.ADMIN:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied"
#             )
#
#     response = await call_next(request)
#     return response


admin = Admin(
    app=app,
    session_maker=sessionmanager.session_maker,
    authentication_backend=AdminAuth(settings.AUTH.KEY)
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
