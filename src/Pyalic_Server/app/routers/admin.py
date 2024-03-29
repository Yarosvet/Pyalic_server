"""
Routers for only admin access
"""
from datetime import timedelta, datetime
from copy import copy
from fastapi import APIRouter, HTTPException, Depends, status, security, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from .. import schema, config
from ..db import session_dep, models
from ..loggers import logger
from ..access import auth

router = APIRouter(dependencies=[Depends(auth.get_current_user)])  # Requires user logged in
public_router = APIRouter()  # Not requires login (also used to get token)


async def _get_user_with_prod(current_user: schema.User, session: AsyncSession) -> models.User:
    """Gets user from DB using `User` scheme, with its products"""
    r = await session.execute(
        select(models.User).filter_by(id=current_user.id).options(selectinload(models.User.owned_products)))
    user_in_db = r.scalar_one_or_none()
    assert user_in_db is not None
    return user_in_db


async def _get_user(current_user: schema.User, session: AsyncSession) -> models.User:
    """Gets user from DB using `User` scheme"""
    r = await session.execute(
        select(models.User).filter_by(id=current_user.id))
    user_in_db = r.scalar_one_or_none()
    assert user_in_db is not None
    return user_in_db


@router.get("/product", response_model=schema.GetProduct)
async def get_product(p_id: int = Query(alias="id"),
                      session: AsyncSession = Depends(session_dep),
                      current_user: schema.User = Depends(auth.get_current_user)):
    """Request handler for getting product"""
    # Get product from DB
    r = await session.execute(select(models.Product).filter_by(id=p_id).options(
        selectinload(models.Product.signatures)))
    p = r.scalar_one_or_none()
    if p is None:  # If not exists
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    # Check permission to perform this action
    user_in_db = await _get_user_with_prod(current_user, session)
    if not user_in_db.get_verifiable_permissions().able_get_product(p):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You have no permission")
    # If all is ok, return product
    sig_period = p.sig_period.total_seconds() if p.sig_period is not None else None
    return schema.GetProduct(name=p.name, sig_install_limit=p.sig_install_limit,
                             sig_sessions_limit=p.sig_sessions_limit, sig_period=sig_period,
                             additional_content=p.additional_content, id=p.id, signatures=len(p.signatures))


@router.post("/product", response_model=schema.GetProduct)
async def add_product(payload: schema.AddProduct,
                      session: AsyncSession = Depends(session_dep),
                      current_user: schema.User = Depends(auth.get_current_user)):
    """Request handler for adding product"""
    # Check if product with specified name already exists
    r = await session.execute(select(models.Product).filter_by(name=payload.name))
    if r.unique().scalars().first() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Product with specified name already exists")
    # Check permission to perform this action
    user_in_db = await _get_user_with_prod(current_user, session)
    if not user_in_db.get_verifiable_permissions().able_add_product():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You have no permission")
    # Create a product
    p = models.Product(name=payload.name,
                       sig_install_limit=payload.sig_install_limit,
                       sig_sessions_limit=payload.sig_sessions_limit,
                       sig_period=timedelta(seconds=payload.sig_period) if payload.sig_period is not None else None,
                       additional_content=payload.additional_content)
    session.add(p)
    await session.commit()
    await session.refresh(p)
    user_in_db.owned_products.append(p)
    await session.commit()
    await session.refresh(p)
    await logger.info(f"Added new product \"{p.name}\" with id={p.id}")
    # Return this product
    sig_period = p.sig_period.total_seconds() if p.sig_period is not None else None
    return schema.GetProduct(name=p.name, sig_install_limit=p.sig_install_limit,
                             sig_sessions_limit=p.sig_sessions_limit, sig_period=sig_period,
                             additional_content=p.additional_content, id=p.id, signatures=0)


@router.put("/product", response_model=schema.GetProduct)
async def update_product(payload: schema.UpdateProduct,
                         p_id: int = Query(alias="id"),
                         session: AsyncSession = Depends(session_dep),
                         current_user: schema.User = Depends(auth.get_current_user)):
    """Request handler for updating existing product"""
    # Get product
    r = await session.execute(select(models.Product).filter_by(id=p_id).options(
        selectinload(models.Product.signatures)))
    p = r.scalar_one_or_none()
    if p is None:  # If not exists
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    # Check permission to perform this action
    user_in_db = await _get_user_with_prod(current_user, session)
    if not user_in_db.get_verifiable_permissions().able_edit_product(p):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You have no permission")
    # Check every field if it is filled (autofill mechanics here)
    if 'name' not in payload.unspecified_fields:
        # Check isn't there an existing product with the same name
        r = await session.execute(select(models.Product).filter_by(name=payload.name))
        if r.unique().scalars().first() is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Product with specified name already exists")
        p.name = copy(payload.name)
    if 'sig_install_limit' not in payload.unspecified_fields:
        p.sig_install_limit = copy(payload.sig_install_limit)
    if 'sig_sessions_limit' not in payload.unspecified_fields:
        p.sig_sessions_limit = copy(payload.sig_sessions_limit)
    if 'sig_period' not in payload.unspecified_fields:
        p.sig_period = timedelta(seconds=payload.sig_period) if payload.sig_period is not None else None
    if 'additional_content' not in payload.unspecified_fields:
        p.additional_content = copy(payload.additional_content)
    # Update the product
    await session.commit()
    await session.refresh(p)
    sig_period = p.sig_period.total_seconds() if p.sig_period is not None else None
    await logger.info(f"Updated product \"{p.name}\" with id={p.id}")
    return schema.GetProduct(name=p.name, sig_install_limit=p.sig_install_limit,
                             sig_sessions_limit=p.sig_sessions_limit, sig_period=sig_period,
                             additional_content=p.additional_content, id=p.id, signatures=len(p.signatures))


@router.delete("/product", response_model=schema.Successful)
async def delete_product(p_id: int = Query(alias="id"),
                         session: AsyncSession = Depends(session_dep),
                         current_user: schema.User = Depends(auth.get_current_user)):
    """Request handler for deleting existing product"""
    # Get product with all relations
    r = await session.execute(select(models.Product).filter_by(id=p_id).options(
        selectinload(models.Product.signatures).selectinload(models.Signature.installations)))
    p = r.scalar_one_or_none()
    if p is None:  # If not exists
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    # Check permission to perform this action
    user_in_db = await _get_user_with_prod(current_user, session)
    if not user_in_db.get_verifiable_permissions().able_delete_product(p):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You have no permission")
    # Firstly clean signatures
    for sig in p.signatures:
        # And installations
        for inst in sig.installations:
            await session.delete(inst)
        await session.delete(sig)
    p_name = p.name
    p_id = p.id
    # Delete the product
    await session.delete(p)
    await session.commit()
    await logger.info(f"Deleted product \"{p_name}\" with id={p_id}")
    return schema.Successful()  # Return {success: true}


@router.get("/list_products", response_model=schema.ListProducts)
async def list_products(limit: int = 100, offset: int = 0, session: AsyncSession = Depends(session_dep)):
    """Request handler for getting list of all products"""
    # Get all products from DB
    r = await session.execute(
        select(models.Product).order_by(models.Product.id).offset(offset).limit(limit).options(
            selectinload(models.Product.signatures)))
    p_list = []
    # List them
    for p in r.scalars():
        sig_period = p.sig_period.total_seconds() if p.sig_period is not None else None
        p_list.append(schema.ListedProduct(id=p.id, name=p.name, sig_install_limit=p.sig_install_limit,
                                           sig_sessions_limit=p.sig_sessions_limit, sig_period=sig_period,
                                           signatures=len(p.signatures)))
    return schema.ListProducts(products=p_list, items=len(p_list))


@router.get("/list_signatures", response_model=schema.ListSignatures)
async def list_signatures(product_id: int,
                          limit: int = 100,
                          offset: int = 0,
                          session: AsyncSession = Depends(session_dep),
                          current_user: schema.User = Depends(auth.get_current_user)):
    """Request handler for getting list of signatures of specified product"""
    # Get product from DB
    r = await session.execute(select(models.Product).filter_by(id=product_id))
    p = r.scalar_one_or_none()
    if p is None:  # If not exists
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    user_in_db = await _get_user_with_prod(current_user, session)
    # Check permission to perform this action
    if not user_in_db.get_verifiable_permissions().able_get_product(p):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You have no permission")
    # Get signatures
    r = await session.execute(select(models.Signature).filter_by(product_id=product_id)
                              .order_by(models.Signature.id).offset(offset).limit(limit))
    sig_list = []
    for sig in r.scalars():
        sig_list.append(schema.ShortSignature(comment=sig.comment, id=sig.id))
    # Return list of signatures
    return schema.ListSignatures(items=len(sig_list), signatures=sig_list, product_id=product_id)


@router.get("/signature", response_model=schema.GetSignature)
async def get_signature(s_id: int = Query(alias="id"),
                        session: AsyncSession = Depends(session_dep),
                        current_user: schema.User = Depends(auth.get_current_user)):
    """Request handler for getting signature info"""
    # Get signature from DB
    r = await session.execute(
        select(models.Signature).filter_by(id=s_id).options(
            selectinload(models.Signature.installations), selectinload(models.Signature.product)))
    sig = r.scalar_one_or_none()
    if sig is None:  # If not exists
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signature not found")
    # Check permission to perform this action
    user_in_db = await _get_user_with_prod(current_user, session)
    if not user_in_db.get_verifiable_permissions().able_get_product(sig.product):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You have no permission")
    act_date = None if sig.activation_date is None else sig.activation_date.isoformat()
    # Return signature
    return schema.GetSignature(id=sig.id, license_key=sig.license_key, additional_content=sig.additional_content,
                               comment=sig.comment, installed=len(sig.installations), product_id=sig.product_id,
                               activation_date=act_date)


@router.post("/signature", response_model=schema.GetSignature)
async def add_signature(payload: schema.AddSignature,
                        session: AsyncSession = Depends(session_dep),
                        current_user: schema.User = Depends(auth.get_current_user)):
    """Request handler for adding new signature of specified product"""
    # Check if there's a signature with the same license key
    r = await session.execute(select(models.Signature).filter_by(license_key=payload.license_key))
    if r.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Signature with specified license key already exists")
    # Get product from DB
    r = await session.execute(select(models.Product).filter_by(id=payload.product_id))
    p = r.scalar_one_or_none()
    if p is None:  # If not exists
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    # Check permission to perform this action
    user_in_db = await _get_user_with_prod(current_user, session)
    if not user_in_db.get_verifiable_permissions().able_edit_product(p):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You have no permission")
    # Create signature
    sig = models.Signature(license_key=payload.license_key, additional_content=payload.additional_content,
                           comment=payload.comment, product_id=payload.product_id,
                           activation_date=None if not payload.activate else datetime.utcnow())
    session.add(sig)
    await session.commit()
    await session.refresh(sig)
    act_date = None if sig.activation_date is None else sig.activation_date.isoformat()
    await logger.info(f"Added new signature with id={sig.id} of product_id={payload.product_id}")
    # Return signature
    return schema.GetSignature(id=sig.id, license_key=sig.license_key, additional_content=sig.additional_content,
                               comment=sig.comment, installed=0, product_id=sig.product_id, activation_date=act_date)


@router.put("/signature", response_model=schema.GetSignature)
async def update_signature(payload: schema.UpdateSignature,
                           s_id: int = Query(alias="id"),
                           session: AsyncSession = Depends(session_dep),
                           current_user: schema.User = Depends(auth.get_current_user)):
    """Request handler for updating an existing signature"""
    # Get signature from db
    r = await session.execute(
        select(models.Signature).filter_by(id=s_id).options(
            selectinload(models.Signature.installations), selectinload(models.Signature.product)))
    sig = r.scalar_one_or_none()
    if sig is None:  # If not exists
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signature not found")
    # Check permission to perform this action
    user_in_db = await _get_user_with_prod(current_user, session)
    if not user_in_db.get_verifiable_permissions().able_edit_product(sig.product):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You have no permission")
    # Check every field if it is filled (autofill mechanics)
    if 'license_key' not in payload.unspecified_fields:
        # Check if another signature has the same license key
        r = await session.execute(select(models.Signature).filter_by(license_key=payload.license_key))
        if r.unique().scalars().first() is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Signature with specified license key already exists")
        sig.license_key = copy(payload.license_key)
    if 'comment' not in payload.unspecified_fields:
        sig.comment = copy(payload.comment)
    if 'additional_content' not in payload.unspecified_fields:
        sig.additional_content = copy(payload.additional_content)
    # Update signature
    await session.commit()
    await session.refresh(sig)
    await logger.info(f"Updated signature with id={sig.id}")
    # Return signature
    act_date = None if sig.activation_date is None else sig.activation_date.isoformat()
    return schema.GetSignature(id=sig.id, license_key=sig.license_key, additional_content=sig.additional_content,
                               comment=sig.comment, installed=len(sig.installations), product_id=sig.product_id,
                               activation_date=act_date)


@router.delete("/signature", response_model=schema.Successful)
async def delete_signature(s_id: int = Query(alias="id"),
                           session: AsyncSession = Depends(session_dep),
                           current_user: schema.User = Depends(auth.get_current_user)):
    """Request handler for deleting an existing signature"""
    # Get signature form DB
    r = await session.execute(select(models.Signature).filter_by(id=s_id))
    sig = r.scalar_one_or_none()
    if sig is None:  # If not exists
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signature not found")
    # If exists, get it with relations
    r = await session.execute(select(models.Signature).filter_by(id=s_id)
                              .options(selectinload(models.Signature.installations),
                                       selectinload(models.Signature.product)))
    sig = r.scalar_one_or_none()
    # Check permission to perform this action
    user_in_db = await _get_user_with_prod(current_user, session)
    if not user_in_db.get_verifiable_permissions().able_edit_product(sig.product):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You have no permission")
    # Firstly delete all installations
    for inst in sig.installations:
        await session.delete(inst)
    # Delete signature
    await session.delete(sig)
    await session.commit()
    await logger.info(f"Deleted signature with id={sig.id}")
    return schema.Successful()  # Return {success: true}


@public_router.post("/token", response_model=schema.Token)
async def login_for_access_token(form_data: security.OAuth2PasswordRequestForm = Depends(),
                                 session: AsyncSession = Depends(session_dep)):
    """Authorization request handler for getting JWT token"""
    user = await auth.authenticate_user(form_data.username, form_data.password, session)
    if not user:  # If authentication failed
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Create token
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me/", response_model=schema.User)
async def users_me(current_user: schema.User = Depends(auth.get_current_user)):
    """Responding `whoami` request"""
    return current_user


@router.get("/users/list", response_model=schema.ListUsers)
async def list_users(limit: int = 100, offset: int = 0, session: AsyncSession = Depends(session_dep)):
    """Request handler for getting list of all users"""
    r = await session.execute(select(models.User).order_by(models.User.id).offset(offset).limit(limit))
    users = []
    # List all users
    for u in r.scalars():
        users.append(schema.User(id=u.id, username=u.username))
    return schema.ListUsers(items=len(users), users=users)


@router.get("/users/user", response_model=schema.ExpandedUser)
async def get_user(u_id: int = Query(alias="id"),
                   session: AsyncSession = Depends(session_dep)):
    """Request handler for getting User by his ID"""
    # Get user from DB
    r = await session.execute(select(models.User).filter_by(id=u_id))
    u = r.scalar_one_or_none()
    if u is None:  # If not exists
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return schema.ExpandedUser(id=u.id, username=u.username, master_id=u.master_id, permissions=u.permissions)


@router.post("/users/user", response_model=schema.ExpandedUser)
async def add_user(payload: schema.AddUser,
                   session: AsyncSession = Depends(session_dep),
                   current_user: schema.User = Depends(auth.get_current_user)):
    """Request handler for adding new user with specified parameters"""
    # Check permission to perform this action
    current_user_in_db = await _get_user(current_user, session)
    if not current_user_in_db.get_verifiable_permissions().able_add_user(payload.permissions):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You have no permission")
    # Check if someone already has this username
    r = await session.execute(select(models.User).filter_by(username=payload.username))
    if r.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="User with specified username already exists")
    # Create user
    u = models.User(username=payload.username,
                    hashed_password=auth.get_password_hash(payload.password),
                    permissions=payload.permissions,
                    master_id=current_user_in_db.id)
    session.add(u)
    await session.commit()
    await session.refresh(u)
    # Return user
    return schema.ExpandedUser(id=u.id, username=u.username, master_id=u.master_id, permissions=u.permissions)


@router.put("/users/user", response_model=schema.ExpandedUser)
async def update_user(payload: schema.UpdateUser,
                      u_id: int = Query(alias="id"),
                      session: AsyncSession = Depends(session_dep),
                      current_user: schema.User = Depends(auth.get_current_user)):
    """Request handler for updating an existing user"""
    # Get user form db
    r = await session.execute(select(models.User).filter_by(id=u_id))
    u = r.scalar_one_or_none()
    if u is None:  # If not exists
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # Check permission to perform this action
    current_user_in_db = await _get_user(current_user, session)
    if not current_user_in_db.get_verifiable_permissions().able_edit_user(u, payload.permissions):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You have no permission")
    # Check every field if it is filled (autofill mechanics)
    if 'username' not in payload.unspecified_fields:
        # Check if someone already has this username
        r = await session.execute(select(models.User).filter_by(username=payload.username))
        if r.scalar_one_or_none() is not None:
            raise HTTPException(status_code=409, detail="User with specified username already exists")
        u.username = copy(payload.username)
    if 'password' not in payload.unspecified_fields:
        u.hashed_password = auth.get_password_hash(payload.password)
    if 'permissions' not in payload.unspecified_fields:
        u.permissions = copy(payload.permissions)
    await session.commit()
    await session.refresh(u)
    # Return user
    return schema.ExpandedUser(id=u.id, username=u.username, master_id=u.master_id, permissions=u.permissions)


@router.delete("/users/user", response_model=schema.Successful)
async def delete_user(u_id: int = Query(alias="id"),
                      session: AsyncSession = Depends(session_dep),
                      current_user: schema.User = Depends(auth.get_current_user)):
    """Request handler for deleting an existing user"""
    # Get user from DB
    r = await session.execute(select(models.User).filter_by(id=u_id))
    u = r.scalar_one_or_none()
    if u is None:  # If not exists
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # Check every field if it is filled (autofill mechanics)
    current_user_in_db = await _get_user(current_user, session)
    if not current_user_in_db.get_verifiable_permissions().able_delete_user(u):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You have no permission")
    # Delete user
    await session.delete(u)
    await session.commit()
    return schema.Successful()  # Return {success: true}
