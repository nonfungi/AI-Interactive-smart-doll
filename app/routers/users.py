# app/routers/users.py

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas, models, auth

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

# --- User CRUD Functions ---
async def create_user(db: AsyncSession, user: schemas.UserCreate) -> models.User:
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# --- User Endpoints ---
@router.post("/register", response_model=schemas.UserPublic, status_code=status.HTTP_201_CREATED)
async def register_user(user: schemas.UserCreate, db: AsyncSession = Depends(auth.get_db)):
    db_user = await auth.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await create_user(db=db, user=user)

@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: AsyncSession = Depends(auth.get_db)):
    user = await auth.get_user_by_email(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserPublic)
async def read_users_me(current_user: Annotated[models.User, Depends(auth.get_current_user)]):
    return current_user
