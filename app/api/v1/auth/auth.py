from datetime import timedelta

from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from .schemas import Token, User, Status, CreateUserPayload, UsersList
from app.api.v1.dependencies.db import get_db
from edgedb.asyncio_client import AsyncIOClient
from edgedb.errors import ConstraintViolationError
from .dependencies import get_user, get_password_hash, create_access_token, get_current_active_user, get_users

ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter()




@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db_client=Depends(get_db)):
    user = await get_user(db_client, form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me/", response_model=User)
async def read_users_me(current_user = Depends(get_current_active_user)):
    return current_user


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def post_user(user: CreateUserPayload = Depends(CreateUserPayload.as_form), db_client: AsyncIOClient = Depends(get_db)) -> User:
    try:
        (created_user,) = await db_client.query(
            """
            WITH
            new_user := (INSERT User {
                first_name := <str>$first_name,
                last_name := <str>$last_name,
                status := <str>$status,
                username := <str>$username,
                hashed_password := <str>$hashed_password
                })
            SELECT new_user {
                id,
                first_name,
                last_name,
                username,
                status

            };
            """,
            first_name=user.first_name,
            last_name=user.last_name,
            status=Status.active.value,
            username=user.username,
            hashed_password=get_password_hash(user.password)

        )
    except ConstraintViolationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"Username '{user.username}' already exists,"},
        )
    response = User(
        id=created_user.id,
        first_name=created_user.first_name,
        last_name=created_user.last_name,
        username=created_user.username,
        status=created_user.status,
    )
    return response


@router.get("/users/", response_model=UsersList)
async def get_all_users(users = Depends(get_users)):
    return UsersList(data=users)

