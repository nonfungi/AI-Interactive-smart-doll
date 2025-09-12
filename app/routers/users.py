# app/routers/users.py
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# --- Import from our own modules ---
# Notice we no longer need to import config directly.
# All dependencies are handled by the auth module.
from .. import schemas, models, auth

# Create a new router for user-related endpoints
router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

# --- User CRUD Functions (specific to this router) ---
async def create_user(db: AsyncSession, user: schemas.UserCreate) -> models.User:
    """Creates a new user in the database."""
    # Hash the password using the utility from the auth module
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# --- User Endpoints ---
@router.post("/register", response_model=schemas.UserPublic, status_code=status.HTTP_201_CREATED)
async def register_user(user: schemas.UserCreate, db: AsyncSession = Depends(auth.get_db)):
    """Endpoint to register a new user."""
    # Check if a user with this email already exists
    db_user = await auth.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    # If not, create the new user
    return await create_user(db=db, user=user)

@router.get("/me", response_model=schemas.UserPublic)
async def read_users_me(current_user: Annotated[models.User, Depends(auth.get_current_user)]):
    """
    Endpoint to get the profile of the currently logged-in user.
    The `get_current_user` dependency protects this endpoint.
    """
    return current_user

