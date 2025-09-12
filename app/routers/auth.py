# app/routers/auth.py

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

# --- Import modules from the parent directory ---
# This is where we connect the logic from app/auth.py to the endpoint
from .. import auth, schemas, database, config

# Create the router for authentication endpoints
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(
    # FastAPI will automatically get the form data (username, password)
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    # Dependency to get a database session
    db: Annotated[AsyncSession, Depends(database.get_db)],
    # Dependency to get the application settings (for the secret key)
    settings: Annotated[config.Settings, Depends(config.get_settings)]
):
    """
    Handles the user login process.
    It takes a username and password, verifies them, and returns a JWT token.
    """
    # Use the logic from `app/auth.py` to find the user
    user = await auth.get_user_by_email(db, email=form_data.username)
    
    # Verify the user and their password
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # If credentials are correct, create an access token using the logic from `app/auth.py`
    access_token = auth.create_access_token(
        data={"sub": user.email},
        settings=settings  # Pass the settings object to the function
    )
    
    # Return the token to the client
    return {"access_token": access_token, "token_type": "bearer"}