from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every

from .routers import admin, user
from .licensing import sessions as lic_sessions
from . import loggers, db, config

app = FastAPI()
app.include_router(admin.router, prefix='/admin')
app.include_router(admin.public_router, prefix='/admin')
app.include_router(user.router)



@app.on_event('startup')
async def init_models_db():
    await db.global_init(config.DB_USER, config.DB_PASSWORD, config.DB_HOST, config.DB_NAME)


@app.on_event('startup')
@repeat_every(seconds=2)
async def periodic_clean_expired_sessions():
    await lic_sessions.clean_expired_sessions()


@app.exception_handler(Exception)
async def exception_handler(request, exc):
    await loggers.logger.exception(f"Exception occurred in {request.method} {request.url}: {exc}")
    return None
