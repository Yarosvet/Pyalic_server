from fastapi import APIRouter, HTTPException, status

from .. import schema
from ..licensing import engine as lic_engine
from ..licensing import sessions as lic_sessions

router = APIRouter()


@router.get("/check_license")
async def check_license(payload: schema.CheckLicense):
    confirmed, error = await lic_engine.process_check_request(payload.license_key, payload.fingerprint)
    if confirmed:
        return schema.Successful()
    return schema.BadLicense(error=error)


@router.post("/keepalive", response_model=schema.Successful)
async def keepalive(payload: schema.SessionIdField):
    try:
        await lic_sessions.keep_alive(payload.session_id)
    except lic_sessions.SessionNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return schema.Successful


@router.post("/end_session", response_model=schema.Successful)
async def end_session(payload: schema.SessionIdField):
    try:
        await lic_sessions.end_session(payload.session_id)
    except lic_sessions.SessionNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return schema.Successful
