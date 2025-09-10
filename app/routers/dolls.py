# app/routers/dolls.py

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .. import schemas, models, auth

router = APIRouter(
    prefix="/dolls",
    tags=["Dolls"]
)

# --- Doll CRUD Functions ---
async def get_doll_by_device_id(db: AsyncSession, device_id: str) -> models.Doll | None:
    result = await db.execute(select(models.Doll).filter(models.Doll.device_id == device_id))
    return result.scalars().first()

async def register_new_doll(db: AsyncSession, doll_data: schemas.DollCreate) -> models.Doll:
    db_doll = models.Doll(**doll_data.model_dump())
    db.add(db_doll)
    await db.commit()
    await db.refresh(db_doll)
    return db_doll

async def assign_doll_to_child(db: AsyncSession, doll: models.Doll, child_id: int) -> models.Doll:
    doll.child_id = child_id
    await db.commit()
    await db.refresh(doll)
    return doll

# --- Doll Endpoints ---
@router.post("/register", response_model=schemas.DollPublic, status_code=status.HTTP_201_CREATED)
async def register_doll(doll: schemas.DollCreate, db: AsyncSession = Depends(auth.get_db)):
    db_doll = await get_doll_by_device_id(db, device_id=doll.device_id)
    if db_doll:
        raise HTTPException(status_code=400, detail="Doll with this device ID already exists")
    return await register_new_doll(db=db, doll_data=doll)

@router.post("/assign", response_model=schemas.DollPublic)
async def assign_doll(
    assignment: schemas.DollAssign,
    current_user: Annotated[models.User, Depends(auth.get_current_user)],
    db: AsyncSession = Depends(auth.get_db)
):
    doll = await get_doll_by_device_id(db, device_id=assignment.device_id)
    if not doll:
        raise HTTPException(status_code=404, detail="Doll not found")

    child_ids = [child.id for child in current_user.children]
    if assignment.child_id not in child_ids:
        raise HTTPException(status_code=403, detail="Child does not belong to the current user")
        
    return await assign_doll_to_child(db=db, doll=doll, child_id=assignment.child_id)
