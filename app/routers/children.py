# app/routers/children.py

from typing import Annotated, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas, models, auth

router = APIRouter(
    prefix="/children",
    tags=["Children"],
    dependencies=[Depends(auth.get_current_user)] # Secure all routes in this file
)

# --- Child CRUD Functions ---
async def create_child_for_user(db: AsyncSession, child_data: schemas.ChildCreate, user_id: int) -> models.Child:
    db_child = models.Child(**child_data.model_dump(), user_id=user_id)
    db.add(db_child)
    await db.commit()
    await db.refresh(db_child)
    return db_child

# --- Child Endpoints ---
@router.post("", response_model=schemas.ChildPublic, status_code=status.HTTP_201_CREATED)
async def create_child(
    child: schemas.ChildCreate,
    current_user: Annotated[models.User, Depends(auth.get_current_user)],
    db: AsyncSession = Depends(auth.get_db)
):
    return await create_child_for_user(db=db, child_data=child, user_id=current_user.id)

@router.get("", response_model=List[schemas.ChildPublic])
async def read_children_for_user(current_user: Annotated[models.User, Depends(auth.get_current_user)]):
    return current_user.children
