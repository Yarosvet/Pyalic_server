"""
Python Advanced Licensing System server
(Main Fastapi App configuration module)
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import admin, user
from . import loggers, db, config
from .access import create_default_user_if_not_exists


@asynccontextmanager
async def lifespan(application: FastAPI):  # pylint: disable=unused-argument
    """Lifespan of FastAPI application"""
    await db.global_init(config.DB_USER, config.DB_PASSWORD, config.DB_HOST, config.DB_NAME)
    await create_default_user_if_not_exists()
    yield


app = FastAPI(lifespan=lifespan)

# CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router, prefix='/admin')
app.include_router(admin.public_router, prefix='/admin')
app.include_router(user.router)


@app.exception_handler(Exception)
async def exception_handler(request, exc):
    """Handle exceptions occurred in runtime"""
    await loggers.logger.exception(f"Exception occurred in {request.method} {request.url}: {exc}")
    return None
