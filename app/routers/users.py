from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas, models, auth

# --- FIX: The prefix is now handled in main.py, so we remove it from here ---
router = APIRouter(
    tags=["Users"]
)

# --- Dependency ---
# We need a get_db function available in this router's context
# It's better to get it from the source (auth.py)
get_db = auth.get_db

# --- User CRUD Functions ---
async def create_user(db: AsyncSession, user: schemas.UserCreate) -> models.User:
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# --- User Endpoints ---
# The path is now just "/register" which will be correctly prefixed with "/users" by main.py
@router.post("/register", response_model=schemas.UserPublic, status_code=status.HTTP_201_CREATED)
async def register_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await auth.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await create_user(db=db, user=user)

# The path is now just "/login"
@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: AsyncSession = Depends(get_db)):
    user = await auth.get_user_by_email(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# The path is now just "/me"
@router.get("/me", response_model=schemas.UserPublic)
async def read_users_me(current_user: Annotated[models.User, Depends(auth.get_current_user)]):
    return current_user

