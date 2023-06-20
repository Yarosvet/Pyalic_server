from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from .. import schema
from ..licensing import engine as lic_engine
from ..licensing import sessions as lic_sessions
from ..db import create_session, models

router = APIRouter()


@router.get("/check_license")
async def check_license(payload: schema.CheckLicense, session: AsyncSession = Depends(create_session)):
    confirmed, error_or_sid = await lic_engine.process_check_request(payload.license_key, payload.fingerprint, session)
    if confirmed:
        r = await session.execute(select(models.Signature).filter_by(license_key=payload.license_key).options(
            selectinload(models.Signature.product)))
        sig = r.scalar_one_or_none()
        if sig is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
        return schema.GoodLicense(session_id=error_or_sid, additional_content_signature=sig.additional_content,
                                  additional_content_product=sig.product.additional_content)
    return schema.BadLicense(error=error_or_sid)


@router.post("/keepalive", response_model=schema.Successful)
async def keepalive(payload: schema.SessionIdField):
    try:
        await lic_sessions.keep_alive(payload.session_id)
    except lic_sessions.SessionNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return schema.Successful()


@router.post("/end_session", response_model=schema.Successful)
async def end_session(payload: schema.SessionIdField):
    try:
        await lic_sessions.end_session(payload.session_id)
    except lic_sessions.SessionNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return schema.Successful()
