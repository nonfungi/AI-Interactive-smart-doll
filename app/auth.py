# app/auth.py
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from passlib.context import CryptContext
from jose import JWTError, jwt

# --- Import from our own modules ---
# The correct way: Import the function and the Pydantic model
from .config import Settings, get_settings
from .database import get_db, AsyncSessionLocal
from . import models, schemas

# --- Security Configuration ---
# This should be defined once here.
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login") # Corrected tokenUrl

# --- Password Utilities ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

# --- Token Creation (Refactored to accept settings) ---
def create_access_token(data: dict, settings: Settings):
    """Creates a new JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

# --- Database User Retrieval ---
async def get_user_by_email(db: AsyncSession, email: str) -> models.User | None:
    """Fetches a user from the database by their email."""
    result = await db.execute(select(models.User).options(selectinload(models.User.children)).filter(models.User.email == email))
    return result.scalars().first()

# --- The Core User Dependency (Refactored to inject settings) ---
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings) # CORRECT: Inject settings via Depends
):
    """
    Decodes the JWT token, validates it, and returns the current user.
    This is the main dependency for protected endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Use the injected settings object to get the secret key and algorithm
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

