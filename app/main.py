# app/main.py

import uvicorn
import io
from contextlib import asynccontextmanager
from typing import Annotated, List
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Depends, HTTPException, status, Header, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from passlib.context import CryptContext
from jose import JWTError, jwt

from .config import settings
from .services import get_ai_response, transcribe_audio, convert_text_to_speech
from .database import AsyncSessionLocal
from .models import User, Child, Doll

# --- Security & Hashing Setup ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Pydantic Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

class ChildCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    age: int = Field(..., gt=0, lt=18)

class ChildPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    age: int

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="User's password")

class DollCreate(BaseModel):
    device_id: str

class DollPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    device_id: str
    child_id: int | None

class DollAssign(BaseModel):
    device_id: str
    child_id: int

class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    children: List[ChildPublic] = []

class AuthRequest(BaseModel):
    auth_token: str = Field(..., description="The secret token sent by the doll.")

# --- Dependency for DB Session ---
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# --- Lifespan Event Handler ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server starting up...")
    yield
    print("Server shutting down...")

# --- App Initialization ---
app = FastAPI(
    title="Tales AI API",
    description="The core API for the smart storytelling toy.",
    version="0.1.0",
    lifespan=lifespan
)

# --- Authentication & CRUD Functions ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).options(selectinload(User.children)).filter(User.email == email))
    return result.scalars().first()

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = await get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

async def create_user(db: AsyncSession, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def create_child_for_user(db: AsyncSession, child_data: ChildCreate, user_id: int) -> Child:
    db_child = Child(**child_data.model_dump(), user_id=user_id)
    db.add(db_child)
    await db.commit()
    await db.refresh(db_child)
    return db_child

async def get_doll_by_device_id(db: AsyncSession, device_id: str) -> Doll | None:
    result = await db.execute(select(Doll).filter(Doll.device_id == device_id))
    return result.scalars().first()

async def register_new_doll(db: AsyncSession, doll_data: DollCreate) -> Doll:
    db_doll = Doll(**doll_data.model_dump())
    db.add(db_doll)
    await db.commit()
    await db.refresh(db_doll)
    return db_doll

async def assign_doll_to_child(db: AsyncSession, doll: Doll, child_id: int) -> Doll:
    doll.child_id = child_id
    await db.commit()
    await db.refresh(doll)
    return doll

# --- API Endpoints ---
@app.get("/", tags=["Health Check"])
async def root():
    return {"status": "ok", "message": "Welcome to the Tales AI API!"}

# --- User Endpoints ---
@app.post("/users/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED, tags=["Users"])
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await create_user(db=db, user=user)

@app.post("/users/login", response_model=Token, tags=["Users"])
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserPublic, tags=["Users"])
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user

# --- Child Endpoints ---
@app.post("/children", response_model=ChildPublic, status_code=status.HTTP_201_CREATED, tags=["Children"])
async def create_child(child: ChildCreate, current_user: Annotated[User, Depends(get_current_user)], db: AsyncSession = Depends(get_db)):
    return await create_child_for_user(db=db, child_data=child, user_id=current_user.id)

@app.get("/children", response_model=List[ChildPublic], tags=["Children"])
async def read_children_for_user(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user.children

# --- Doll Endpoints ---
@app.post("/dolls/register", response_model=DollPublic, status_code=status.HTTP_201_CREATED, tags=["Dolls"])
async def register_doll(doll: DollCreate, db: AsyncSession = Depends(get_db)):
    db_doll = await get_doll_by_device_id(db, device_id=doll.device_id)
    if db_doll:
        raise HTTPException(status_code=400, detail="Doll with this device ID already exists")
    return await register_new_doll(db=db, doll_data=doll)

@app.post("/dolls/assign", response_model=DollPublic, tags=["Dolls"])
async def assign_doll(assignment: DollAssign, current_user: Annotated[User, Depends(get_current_user)], db: AsyncSession = Depends(get_db)):
    doll = await get_doll_by_device_id(db, device_id=assignment.device_id)
    if not doll:
        raise HTTPException(status_code=404, detail="Doll not found")
    child_ids = [child.id for child in current_user.children]
    if assignment.child_id not in child_ids:
        raise HTTPException(status_code=403, detail="Child does not belong to the current user")
    return await assign_doll_to_child(db=db, doll=doll, child_id=assignment.child_id)

@app.post("/auth/doll", tags=["Authentication"])
async def authenticate_doll(request: AuthRequest):
    if request.auth_token == settings.doll_master_auth_token:
        return {"status": "ok", "message": "Doll authenticated successfully."}
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token.")

# --- REVISED: Conversation Endpoint ---
@app.post("/talk", tags=["Conversation"])
async def talk(
    x_auth_token: Annotated[str, Header(description="The secret master token for the doll.")],
    child_id: Annotated[str, Form()],
    audio_file: UploadFile = File(...)
):
    """
    Handles a full voice conversation turn:
    1. Receives audio from the doll.
    2. Transcribes audio to text.
    3. Gets a contextual AI response.
    4. Converts the response text back to audio.
    5. Streams the audio back to the doll.
    """
    # --- DEBUGGING: Print the tokens to see what the server receives ---
    print("--- Token Comparison ---")
    print(f"Token from request header: '{x_auth_token}'")
    print(f"Token from .env settings:  '{settings.doll_master_auth_token}'")
    print("------------------------")

    if x_auth_token != settings.doll_master_auth_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token.")

    # 1. Transcribe Audio to Text
    transcribed_text = await transcribe_audio(audio_file)
    print(f"Transcribed text for child '{child_id}': {transcribed_text}")

    # 2. Get AI Response
    ai_response_text = await get_ai_response(user_text=transcribed_text, child_id=child_id)
    print(f"AI response for child '{child_id}': {ai_response_text}")

    # 3. Convert Text to Speech
    response_audio_bytes = await convert_text_to_speech(ai_response_text)

    # 4. Stream Audio Back
    return StreamingResponse(io.BytesIO(response_audio_bytes), media_type="audio/mpeg")

# --- Main Execution ---
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=settings.api_port, reload=True)
