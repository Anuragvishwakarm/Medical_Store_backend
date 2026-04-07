from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.medicine import Medicine
from app.models.batch import Batch
from app.schemas.medicine import MedicineCreate, MedicineUpdate, MedicineOut, MedicineWithStock

router = APIRouter(prefix="/medicines", tags=["Medicines"])


@router.post("/", response_model=MedicineOut, status_code=201)
async def create_medicine(payload: MedicineCreate, db: AsyncSession = Depends(get_db)):
    medicine = Medicine(**payload.model_dump())
    db.add(medicine)
    await db.flush()
    await db.refresh(medicine)
    return medicine


@router.get("/", response_model=list[MedicineWithStock])
async def list_medicines(
    search: str | None = Query(None),
    category: str | None = Query(None),
    low_stock: bool = Query(False),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    query = select(Medicine).where(Medicine.is_active == True)
    if search:
        query = query.where(Medicine.name.ilike(f"%{search}%"))
    if category:
        query = query.where(Medicine.category == category)

    result = await db.execute(query.offset(skip).limit(limit))
    medicines = result.scalars().all()

    out = []
    for m in medicines:
        # Aggregate stock
        stock_res = await db.execute(
            select(
                func.coalesce(func.sum(Batch.available_units), 0),
                func.min(Batch.expiry_date),
            ).where(
                Batch.medicine_id == m.id,
                Batch.is_active == True,
                Batch.available_units > 0,
                Batch.expiry_date > date.today(),
            )
        )
        total_units, nearest_expiry = stock_res.one()

        item = MedicineWithStock.model_validate(m)
        item.total_available_units = int(total_units)
        item.nearest_expiry_date = str(nearest_expiry) if nearest_expiry else None

        if low_stock and item.total_available_units > m.min_stock_units:
            continue
        out.append(item)

    return out


@router.get("/{medicine_id}", response_model=MedicineWithStock)
async def get_medicine(medicine_id: int, db: AsyncSession = Depends(get_db)):
    medicine = await db.get(Medicine, medicine_id)
    if not medicine:
        raise HTTPException(404, "Medicine not found")

    stock_res = await db.execute(
        select(
            func.coalesce(func.sum(Batch.available_units), 0),
            func.min(Batch.expiry_date),
        ).where(
            Batch.medicine_id == medicine_id,
            Batch.is_active == True,
            Batch.available_units > 0,
            Batch.expiry_date > date.today(),
        )
    )
    total_units, nearest_expiry = stock_res.one()
    item = MedicineWithStock.model_validate(medicine)
    item.total_available_units = int(total_units)
    item.nearest_expiry_date = str(nearest_expiry) if nearest_expiry else None
    return item


@router.patch("/{medicine_id}", response_model=MedicineOut)
async def update_medicine(
    medicine_id: int, payload: MedicineUpdate, db: AsyncSession = Depends(get_db)
):
    medicine = await db.get(Medicine, medicine_id)
    if not medicine:
        raise HTTPException(404, "Medicine not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(medicine, field, value)
    db.add(medicine)
    await db.flush()
    await db.refresh(medicine)
    return medicine


@router.delete("/{medicine_id}", status_code=204)
async def delete_medicine(medicine_id: int, db: AsyncSession = Depends(get_db)):
    medicine = await db.get(Medicine, medicine_id)
    if not medicine:
        raise HTTPException(404, "Medicine not found")
    medicine.is_active = False
    db.add(medicine)
