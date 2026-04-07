from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.batch import Batch
from app.models.medicine import Medicine
from app.schemas.batch import BatchOut

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/expiry", summary="Batches expiring within N days")
async def expiry_alerts(
    days: int = Query(30, ge=1, le=365, description="Alert window in days"),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    cutoff = today + timedelta(days=days)

    result = await db.execute(
        select(Batch, Medicine.name.label("medicine_name"))
        .join(Medicine, Batch.medicine_id == Medicine.id)
        .where(
            Batch.is_active == True,
            Batch.available_units > 0,
            Batch.expiry_date >= today,        # not yet expired
            Batch.expiry_date <= cutoff,       # but will expire within window
        )
        .order_by(Batch.expiry_date.asc())
    )
    rows = result.all()

    return [
        {
            "batch_id": row.Batch.id,
            "medicine_name": row.medicine_name,
            "batch_number": row.Batch.batch_number,
            "expiry_date": str(row.Batch.expiry_date),
            "days_to_expiry": (row.Batch.expiry_date - today).days,
            "available_units": row.Batch.available_units,
            "urgency": "critical" if (row.Batch.expiry_date - today).days <= 7 else "warning",
        }
        for row in rows
    ]


@router.get("/low-stock", summary="Medicines below minimum stock level")
async def low_stock_alerts(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import func

    today = date.today()

    # Aggregate available units per medicine from non-expired batches
    stock_sub = (
        select(
            Batch.medicine_id,
            func.coalesce(func.sum(Batch.available_units), 0).label("total_units"),
        )
        .where(
            Batch.is_active == True,
            Batch.expiry_date > today,
        )
        .group_by(Batch.medicine_id)
        .subquery()
    )

    result = await db.execute(
        select(Medicine, stock_sub.c.total_units)
        .outerjoin(stock_sub, Medicine.id == stock_sub.c.medicine_id)
        .where(
            Medicine.is_active == True,
            func.coalesce(stock_sub.c.total_units, 0) <= Medicine.min_stock_units,
        )
        .order_by(stock_sub.c.total_units.asc())
    )
    rows = result.all()

    return [
        {
            "medicine_id": row.Medicine.id,
            "medicine_name": row.Medicine.name,
            "category": row.Medicine.category,
            "available_units": int(row.total_units or 0),
            "min_stock_units": row.Medicine.min_stock_units,
            "shortage": max(0, row.Medicine.min_stock_units - int(row.total_units or 0)),
        }
        for row in rows
    ]


@router.get("/expired", summary="Batches that have already expired with remaining stock")
async def expired_stock(db: AsyncSession = Depends(get_db)):
    today = date.today()
    result = await db.execute(
        select(Batch, Medicine.name.label("medicine_name"))
        .join(Medicine, Batch.medicine_id == Medicine.id)
        .where(
            Batch.is_active == True,
            Batch.available_units > 0,
            Batch.expiry_date < today,
        )
        .order_by(Batch.expiry_date.asc())
    )
    rows = result.all()
    return [
        {
            "batch_id": row.Batch.id,
            "medicine_name": row.medicine_name,
            "batch_number": row.Batch.batch_number,
            "expiry_date": str(row.Batch.expiry_date),
            "available_units": row.Batch.available_units,
        }
        for row in rows
    ]
