# app/schemas.py

from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List

# --- Schemas for Tokens ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

# --- Schemas for Children ---
class ChildCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    age: int = Field(..., gt=0, lt=18)

class ChildPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    age: int

# --- Schemas for Users (Parents) ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="User's password")

class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    children: List[ChildPublic] = []

# --- Schemas for Dolls ---
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

# --- Schemas for Authentication ---
class AuthRequest(BaseModel):
    auth_token: str = Field(..., description="The secret token sent by the doll.")
