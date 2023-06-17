from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .. import schema
from ..db import create_session, models

router = APIRouter()


@router.get("/interact_product")
async def get_product(payload: schema.IdField, session: AsyncSession = Depends(create_session)):
    r = await session.execute(select(models.Product).filter_by(id=payload.id))
    p = r.scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=404, detail="Product not found")
    sig = await session.run_sync(lambda s: p.signatures)
    sig_period = p.sig_period.total_seconds() if p.sig_period is not None else None
    return schema.Product(success=True, name=p.name, sig_install_limit=p.sig_install_limit,
                          sig_sessions_limit=p.sig_sessions_limit, sig_period=sig_period
                          ,
                          additional_content=p.additional_content, id=p.id, signatures=len(sig))
