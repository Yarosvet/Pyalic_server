"""
User's api for checking license and managing session
"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from .. import schema
from ..licensing import engine as lic_engine
from ..licensing import sessions as lic_sessions
from ..db import session_dep, models
from ..loggers import logger

router = APIRouter()


@router.post("/check_license")
async def check_license(
        payload: schema.CheckLicense,
        session: AsyncSession = Depends(session_dep)
) -> schema.GoodLicense:
    """Request handler for checking license and creating a new Session with ID"""
    try:
        # Process check request via licensing engine
        session_id = await lic_engine.process_check_request(payload.license_key, payload.fingerprint, session)
    except HTTPException as exc:
        # If something went wrong, log it and reraise
        await logger.warning(f"Access denied (key={payload.license_key}), message: {exc.detail}")
        raise exc
    # If access granted (No exceptions raised)
    # Get signature
    r = await session.execute(select(models.Signature).filter_by(license_key=payload.license_key).options(
        selectinload(models.Signature.product)))
    if (sig := r.scalar_one_or_none()) is None:  # If signature not exists
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    return schema.GoodLicense(session_id=session_id, additional_content_signature=sig.additional_content,
                              additional_content_product=sig.product.additional_content)


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
