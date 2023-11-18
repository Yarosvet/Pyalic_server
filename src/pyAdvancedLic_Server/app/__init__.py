"""
Python Advanced Licensing System server
(Main Fastapi App configuration module)
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every

from .routers import admin, user
from .licensing import sessions as lic_sessions
from . import loggers, db, config
from .access import create_default_user_if_not_exists


@asynccontextmanager
async def lifespan(application: FastAPI):  # pylint: disable=unused-argument
    """Lifespan of FastAPI application"""
    await db.global_init(config.DB_USER, config.DB_PASSWORD, config.DB_HOST, config.DB_NAME)
    await create_default_user_if_not_exists()
    await periodic_clean_expired_sessions()  # Call in once, then it will be calling by itself
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(admin.router, prefix='/admin')
app.include_router(admin.public_router, prefix='/admin')
app.include_router(user.router)


@repeat_every(seconds=2)
async def periodic_clean_expired_sessions():
    """Clean expired sessions when time is it"""
    await lic_sessions.clean_expired_sessions()


@app.exception_handler(Exception)
async def exception_handler(request, exc):
    """Handle exceptions occurred in runtime"""
    await loggers.logger.exception(f"Exception occurred in {request.method} {request.url}: {exc}")
    return None
