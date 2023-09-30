from datetime import timedelta, datetime
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .db import models, create_session
from .config import SECRET_KEY
from .schema import TokenData, User

ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="admin/token")


def get_password_hash(password):
    return pwd_context.hash(password)


def check_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def authenticate_user(username: str, password: str, session: AsyncSession):
    r = await session.execute(select(models.User).filter_by(username=username))
    user = r.scalar_one_or_none()
    if not user:
        return False
    if not check_password(password, user.hashed_password):
        return False
    return User(username=user.username)


async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(create_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Wrong credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    r = await session.execute(select(models.User).filter_by(username=token_data.username))
    user = r.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return User(username=user.username)
