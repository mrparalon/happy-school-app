from datetime import datetime, timedelta
from uuid import UUID

from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from .schemas import TokenData, User, Status
from app.api.v1.dependencies.db import get_db
from edgedb.asyncio_client import AsyncIOClient
import orjson
from app.config import settings

# to get a string like this run:
# openssl rand -hex 32

ALGORITHM = "HS256"



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def get_user(db_client: AsyncIOClient, username: str):
    user = await db_client.query(
        """select User {username}
            filter User.username = <str>$username 
            limit 1
            """,
        username=username,
    )
    if user:
        return user[0]

async def get_user_by_id(db_client: AsyncIOClient, user_id: UUID):
    user = await db_client.query_single_json(
        """select User {first_name, last_name, status, id, email, username}
            filter User.id = <uuid>$id 
            limit 1
            """,
        id=user_id,
    )
    return orjson.loads(user)


async def get_users(db_client: AsyncIOClient = Depends(get_db)):
    users = await db_client.query_json(
        """select User {first_name, last_name, status, id, email, username}
            """,
    )
    return orjson.loads(users)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key.get_secret_value(), algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db_client: AsyncIOClient = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key.get_secret_value(), algorithms=[ALGORITHM])
        user_id = UUID(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    user = await get_user_by_id(db_client, token_data.user_id)
    if user is None:
        raise credentials_exception
    return User(**user)


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.status != Status.active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
