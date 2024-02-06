from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_limiter import FastAPILimiter
from fastapi_pagination import add_pagination
from redis import asyncio as aioredis
from sqladmin import Admin

from app.api import router
from app.api.db import sessionmanager
from app.api.db.admin import (AdminAuth, TaskModelView, UserModelView,
                              UserTasksAssociationModelView)
from app.api.db.admin import router as admin_router
from app.api.db.settings_db import settings

LOCAL_REDIS_URL = "redis://127.0.0.1:6379"


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = aioredis.from_url(
        "redis://localhost:6379", encoding="utf8", decode_responses=True
    )
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    await FastAPILimiter.init(redis)

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
add_pagination(app)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8066,
        reload=True,
        workers=3,
    )
