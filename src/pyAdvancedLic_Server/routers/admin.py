from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import timedelta
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .. import schema
from ..db import create_session, models
from .. import config


async def check_access_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    token = credentials.credentials
    if token != config.ACCESS_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token")


router = APIRouter(dependencies=[Depends(check_access_token)])


@router.get("/interact_product", response_model=schema.Product)
async def get_product(payload: schema.IdField, session: AsyncSession = Depends(create_session)):
    r = await session.execute(select(models.Product).filter_by(id=payload.id).options(
        selectinload(models.Product.signatures)))
    p = r.scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    sig_period = p.sig_period.total_seconds() if p.sig_period is not None else None
    return schema.Product(success=True, name=p.name, sig_install_limit=p.sig_install_limit,
                          sig_sessions_limit=p.sig_sessions_limit, sig_period=sig_period,
                          additional_content=p.additional_content, id=p.id, signatures=len(p.signatures))


@router.post("/interact_product", response_model=schema.Product)
async def add_product(payload: schema.Product, session: AsyncSession = Depends(create_session)):
    r = await session.execute(select(models.Product).filter_by(name=payload.name))
    p = r.scalar_one_or_none()
    if p is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Product with specified name already exists")
    p = models.Product(name=payload.name, sig_install_limit=payload.sig_install_limit,
                       sig_sessions_limit=payload.sig_sessions_limit,
                       sig_period=timedelta(seconds=payload.sig_period) if payload.sig_period is not None else None,
                       additional_content=payload.additional_content)
    session.add(p)
    await session.commit()
    await session.refresh(p)
    sig_period = p.sig_period.total_seconds() if p.sig_period is not None else None
    return schema.Product(success=True, name=p.name, sig_install_limit=p.sig_install_limit,
                          sig_sessions_limit=p.sig_sessions_limit, sig_period=sig_period,
                          additional_content=p.additional_content, id=p.id, signatures=0)


@router.put("/interact_product", response_model=schema.Product)
async def update_product(payload: schema.Product, session: AsyncSession = Depends(create_session)):
    r = await session.execute(select(models.Product).filter_by(id=payload.id).options(
        selectinload(models.Product.signatures)))
    p = r.scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    p.name = payload.name
    p.sig_install_limit = payload.sig_install_limit
    p.sig_sessions_limit = payload.sig_sessions_limit
    p.sig_period = timedelta(seconds=payload.sig_period) if payload.sig_period is not None else None
    p.additional_content = payload.additional_content
    await session.commit()
    await session.refresh(p)
    sig_period = p.sig_period.total_seconds() if p.sig_period is not None else None
    return schema.Product(success=True, name=p.name, sig_install_limit=p.sig_install_limit,
                          sig_sessions_limit=p.sig_sessions_limit, sig_period=sig_period,
                          additional_content=p.additional_content, id=p.id, signatures=len(p.signatures))


@router.delete("/interact_product", response_model=schema.Successful)
async def delete_product(payload: schema.IdField, session: AsyncSession = Depends(create_session)):
    r = await session.execute(select(models.Product).filter_by(id=payload.id).options(
        selectinload(models.Product.signatures)))
    p = r.scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    for sig in p.signatures:
        await session.delete(sig)
    await session.delete(p)
    await session.commit()
    return schema.Successful()


@router.get("/all_products", response_model=schema.ListProducts)
async def all_products(payload: schema.ListLimitOffset, session: AsyncSession = Depends(create_session)):
    r = await session.execute(
        select(models.Product).order_by(models.Product.id).offset(payload.offset).limit(payload.limit).options(
            selectinload(models.Product.signatures)))
    p_list = []
    for p in r.scalars():
        sig_period = p.sig_period.total_seconds() if p.sig_period is not None else None
        p_list.append(schema.Product(id=p.id, name=p.name, sig_install_limit=p.sig_install_limit,
                                     sig_sessions_limit=p.sig_sessions_limit, sig_period=sig_period,
                                     signatures=len(p.signatures)))
    return schema.ListProducts(products=p_list, items=len(p_list))
