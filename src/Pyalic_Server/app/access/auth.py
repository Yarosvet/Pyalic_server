"""
Manage Oauth2
"""
from datetime import timedelta, datetime
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ..db import models, session_dep
from ..config import SECRET_KEY
from ..schema import TokenData, User

ALGORITHM = "HS256"
TOKEN_LIFETIME = 15  # Minutes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="admin/token")

CredentialsException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Wrong credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_password_hash(password):  # pylint: disable=C0116
    return pwd_context.hash(password)


def check_password(password: str, hashed: str) -> bool:
    """
    Verify if the password matches to the hash
    :param password:
    :param hashed:
    :return:
    """
    return pwd_context.verify(password, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create JWT token
    :param data: Data to be placed into JWT token
    :param expires_delta: period while the token is alive
    :return: KWT string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=TOKEN_LIFETIME)
    to_encode.update({"exp": expire})  # Set expiration time
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def authenticate_user(username: str, password: str, session: AsyncSession) -> bool | User:
    """
    Authenticate user
    :return: `False` if authentication failed, or `User` scheme if authentication passed
    """
    # Get user from DB
    r = await session.execute(select(models.User).filter_by(username=username))
    user = r.scalar_one_or_none()
    if not user:  # User doesn't exist
        return False
    if not check_password(password, user.hashed_password):  # Wrong password
        return False
    return User(username=user.username, id=user.id)


async def get_current_user(token: str = Depends(oauth2_scheme),
                           session: AsyncSession = Depends(session_dep)) -> User:
    """
    Dependency checking if the user is authenticated and getting his scheme
    :return: `User` scheme
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # Decode payload
        username: str = payload.get("sub")
        if username is None:
            raise CredentialsException
        token_data = TokenData(username=username)
    except JWTError as exc:  # Error while decoding
        raise CredentialsException from exc
    # Get user from DB
    r = await session.execute(select(models.User).filter_by(username=token_data.username))
    user = r.scalar_one_or_none()
    if user is None:  # If there's no such user, throw exception
        raise CredentialsException
    return User(username=user.username, id=user.id)
