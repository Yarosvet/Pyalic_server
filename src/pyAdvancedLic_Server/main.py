from fastapi import FastAPI
import asyncio

from . import db
from . import config
from .routers import admin, user

app = FastAPI()
app.include_router(admin.router, prefix='/admin')
app.include_router(user.router)


@app.on_event('startup')
async def init_models_db():
    await db.global_init(config.DB_USER, config.DB_PASSWORD, config.DB_HOST, config.DB_NAME)
