from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import timedelta, datetime
from fastapi.security import OAuth2PasswordRequestForm

from .. import schema, config
from ..db import create_session, models
from ..loggers import logger
from ..access import auth

router = APIRouter(dependencies=[Depends(auth.get_current_user)])
public_router = APIRouter()


@router.get("/interact_product", response_model=schema.GetProduct)
async def get_product(payload: schema.IdField, session: AsyncSession = Depends(create_session)):
    r = await session.execute(select(models.Product).filter_by(id=payload.id).options(
        selectinload(models.Product.signatures)))
    p = r.scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    sig_period = p.sig_period.total_seconds() if p.sig_period is not None else None
    return schema.GetProduct(name=p.name, sig_install_limit=p.sig_install_limit,
                             sig_sessions_limit=p.sig_sessions_limit, sig_period=sig_period,
                             additional_content=p.additional_content, id=p.id, signatures=len(p.signatures))


@router.post("/interact_product", response_model=schema.GetProduct)
async def add_product(payload: schema.AddProduct,
                      session: AsyncSession = Depends(create_session),
                      current_user: schema.User = Depends(auth.get_current_user)):
    r = await session.execute(select(models.Product).filter_by(name=payload.name))
    if r.unique().scalars().first() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Product with specified name already exists")
    p = models.Product(name=payload.name,
                       sig_install_limit=payload.sig_install_limit,
                       sig_sessions_limit=payload.sig_sessions_limit,
                       sig_period=timedelta(seconds=payload.sig_period) if payload.sig_period is not None else None,
                       additional_content=payload.additional_content)
    session.add(p)
    await session.commit()
    await session.refresh(p)
    r = await session.execute(select(models.User).filter_by(id=current_user.id))
    user_in_db = r.unique().scalars().first()
    assert user_in_db is not None
    p.owners.append(user_in_db)
    await session.commit()
    await session.refresh(p)
    sig_period = p.sig_period.total_seconds() if p.sig_period is not None else None
    await logger.info(f"Added new product \"{p.name}\" with id={p.id}")
    return schema.GetProduct(name=p.name, sig_install_limit=p.sig_install_limit,
                             sig_sessions_limit=p.sig_sessions_limit, sig_period=sig_period,
                             additional_content=p.additional_content, id=p.id, signatures=0)


@router.put("/interact_product", response_model=schema.GetProduct)
async def update_product(payload: schema.UpdateProduct, session: AsyncSession = Depends(create_session)):
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
    await logger.info(f"Updated product \"{p.name}\" with id={p.id}")
    return schema.GetProduct(name=p.name, sig_install_limit=p.sig_install_limit,
                             sig_sessions_limit=p.sig_sessions_limit, sig_period=sig_period,
                             additional_content=p.additional_content, id=p.id, signatures=len(p.signatures))


@router.delete("/interact_product", response_model=schema.Successful)
async def delete_product(payload: schema.IdField, session: AsyncSession = Depends(create_session)):
    r = await session.execute(select(models.Product).filter_by(id=payload.id).options(
        selectinload(models.Product.signatures, models.Signature.installations)))
    p = r.scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    for sig in p.signatures:
        for inst in sig.installations:
            await session.delete(inst)
        await session.delete(sig)
    p_name = p.name
    p_id = p.id
    await session.delete(p)
    await session.commit()
    await logger.info(f"Deleted product \"{p_name}\" with id={p_id}")
    return schema.Successful()


@router.get("/list_products", response_model=schema.ListProducts)
async def list_products(payload: schema.ProductsLimitOffset, session: AsyncSession = Depends(create_session)):
    r = await session.execute(
        select(models.Product).order_by(models.Product.id).offset(payload.offset).limit(payload.limit).options(
            selectinload(models.Product.signatures)))
    p_list = []
    for p in r.scalars():
        sig_period = p.sig_period.total_seconds() if p.sig_period is not None else None
        p_list.append(schema.ListedProduct(id=p.id, name=p.name, sig_install_limit=p.sig_install_limit,
                                           sig_sessions_limit=p.sig_sessions_limit, sig_period=sig_period,
                                           signatures=len(p.signatures)))
    return schema.ListProducts(products=p_list, items=len(p_list))


@router.get("/list_signatures", response_model=schema.ListSignatures)
async def list_signatures(payload: schema.SignaturesLimitOffset, session: AsyncSession = Depends(create_session)):
    r = await session.execute(select(models.Product).filter_by(id=payload.product_id))
    if r.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    r = await session.execute(select(models.Signature).filter_by(product_id=payload.product_id)
                              .order_by(models.Signature.id).offset(payload.offset).limit(payload.limit))
    sig_list = []
    for sig in r.scalars():
        sig_list.append(schema.ShortSignature(comment=sig.comment, id=sig.id))
    return schema.ListSignatures(items=len(sig_list), signatures=sig_list, product_id=payload.product_id)


@router.get("/interact_signature", response_model=schema.GetSignature)
async def get_signature(payload: schema.IdField, session: AsyncSession = Depends(create_session)):
    r = await session.execute(
        select(models.Signature).filter_by(id=payload.id).options(selectinload(models.Signature.installations)))
    sig = r.scalar_one_or_none()
    if sig is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signature not found")
    act_date = None if sig.activation_date is None else sig.activation_date.isoformat()
    return schema.GetSignature(id=sig.id, license_key=sig.license_key, additional_content=sig.additional_content,
                               comment=sig.comment, installed=len(sig.installations), product_id=sig.product_id,
                               activation_date=act_date)


@router.post("/interact_signature", response_model=schema.GetSignature)
async def add_signature(payload: schema.AddSignature, session: AsyncSession = Depends(create_session)):
    r = await session.execute(select(models.Signature).filter_by(license_key=payload.license_key))
    if r.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Signature with specified license key already exists")
    sig = models.Signature(license_key=payload.license_key, additional_content=payload.additional_content,
                           comment=payload.comment, product_id=payload.product_id,
                           activation_date=None if not payload.activate else datetime.utcnow())
    session.add(sig)
    await session.commit()
    await session.refresh(sig)
    act_date = None if sig.activation_date is None else sig.activation_date.isoformat()
    await logger.info(f"Added new signature with id={sig.id} of product_id={payload.product_id}")
    return schema.GetSignature(id=sig.id, license_key=sig.license_key, additional_content=sig.additional_content,
                               comment=sig.comment, installed=0, product_id=sig.product_id, activation_date=act_date)


@router.put("/interact_signature", response_model=schema.GetSignature)
async def update_signature(payload: schema.UpdateSignature, session: AsyncSession = Depends(create_session)):
    r = await session.execute(
        select(models.Signature).filter_by(id=payload.id).options(selectinload(models.Signature.installations)))
    sig = r.scalar_one_or_none()
    if sig is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signature not found")
    sig.license_key = payload.license_key
    sig.comment = payload.comment
    sig.additional_content = payload.additional_content
    await session.commit()
    await session.refresh(sig)
    act_date = None if sig.activation_date is None else sig.activation_date.isoformat()
    await logger.info(f"Updated signature with id={sig.id}")
    return schema.GetSignature(id=sig.id, license_key=sig.license_key, additional_content=sig.additional_content,
                               comment=sig.comment, installed=len(sig.installations), product_id=sig.product_id,
                               activation_date=act_date)


@router.delete("/interact_signature", response_model=schema.Successful)
async def delete_signature(payload: schema.IdField, session: AsyncSession = Depends(create_session)):
    r = await session.execute(select(models.Signature).filter_by(id=payload.id))
    sig = r.scalar_one_or_none()
    if sig is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signature not found")
    await session.delete(sig)
    await session.commit()
    await logger.info(f"Deleted signature with id={sig.id}")
    return schema.Successful()


@public_router.post("/token", response_model=schema.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                                 session: AsyncSession = Depends(create_session)):
    user = await auth.authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me/", response_model=schema.User)
async def users_me(current_user: schema.User = Depends(auth.get_current_user)):
    return current_user
