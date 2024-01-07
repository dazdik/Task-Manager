from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.db import sessionmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    if sessionmanager.engine is not None:
        await sessionmanager.close()


app = FastAPI(lifespan=lifespan)
