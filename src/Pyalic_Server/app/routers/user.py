"""
User's api for checking license and managing session
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from .. import schema
from ..licensing import engine as lic_engine
from ..licensing import sessions as lic_sessions
from ..db import create_session, models
from ..loggers import logger

router = APIRouter()


@router.get("/check_license")
async def check_license(payload: schema.CheckLicense, session: AsyncSession = Depends(create_session)):
    """Request handler for checking license and creating a new Session with ID"""
    # Process check request via licensing engine
    check_resp = await lic_engine.process_check_request(payload.license_key, payload.fingerprint, session)
    if check_resp.success:  # If access granted
        # Get signature
        r = await session.execute(select(models.Signature).filter_by(license_key=payload.license_key).options(
            selectinload(models.Signature.product)))
        sig = r.scalar_one_or_none()
        if sig is None:  # If signature not exists
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
        return schema.GoodLicense(session_id=check_resp.session_id, additional_content_signature=sig.additional_content,
                                  additional_content_product=sig.product.additional_content)
    # If something went wrong
    await logger.warning(f"Access denied (key={payload.license_key}), message: {check_resp.error}")
    resp = schema.BadLicense(error=check_resp.error)
    return JSONResponse(content=resp.dict(), status_code=403)


@router.post("/keepalive", response_model=schema.Successful)
async def keepalive(payload: schema.SessionIdField):
    """Request handler for processing keep-alive sessions"""
    try:
        await lic_sessions.keep_alive(payload.session_id)  # Pass keepalive signal to licensing engine
    except lic_sessions.SessionNotFoundException as exc:
        # If session not exists
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found") from exc
    return schema.Successful()  # Return {success: true}


@router.post("/end_session", response_model=schema.Successful)
async def end_session(payload: schema.SessionIdField):
    """Request handler for correctly ending session by Session ID"""
    try:
        await lic_sessions.end_session(payload.session_id)  # Pass end signal to licensing engine
    except lic_sessions.SessionNotFoundException as exc:
        # If session not exists
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found") from exc
    return schema.Successful()  # Return {success: true}
