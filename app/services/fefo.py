"""
FEFO (First Expiry, First Out) Service
=======================================
When selling a medicine, we must pick batches in ascending expiry-date order.
One sale line (OrderItemCreate) can span multiple batches.
"""
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.batch import Batch
from app.models.medicine import Medicine


class InsufficientStockError(Exception):
    def __init__(self, medicine_name: str, requested: int, available: int):
        self.medicine_name = medicine_name
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient stock for '{medicine_name}': "
            f"requested {requested} units, available {available} units."
        )


class ExpiredBatchError(Exception):
    pass


async def get_fefo_batches(
    db: AsyncSession,
    medicine_id: int,
    quantity_units: int,
) -> list[dict]:
    """
    Returns list of dicts describing how many units to take from each batch.
    Batches are sorted by expiry_date ASC (FEFO).
    Only active, non-expired batches with available stock are considered.

    Returns:
        [
            {
                "batch": Batch,
                "units_to_take": int,
                "sale_price_per_unit": float,
                "mrp_per_unit": float,
                "gst_rate": float,
            },
            ...
        ]
    """
    today = date.today()

    # Load medicine for units_per_strip
    medicine = await db.get(Medicine, medicine_id)
    if not medicine:
        raise ValueError(f"Medicine ID {medicine_id} not found.")

    units_per_strip: int = medicine.units_per_strip

    result = await db.execute(
        select(Batch)
        .where(
            Batch.medicine_id == medicine_id,
            Batch.is_active == True,
            Batch.available_units > 0,
            Batch.expiry_date > today,           # exclude already-expired
        )
        .order_by(Batch.expiry_date.asc())       # FEFO
    )
    batches: list[Batch] = list(result.scalars().all())

    total_available = sum(b.available_units for b in batches)
    if total_available < quantity_units:
        raise InsufficientStockError(medicine.name, quantity_units, total_available)

    allocations = []
    remaining = quantity_units

    for batch in batches:
        if remaining <= 0:
            break
        take = min(batch.available_units, remaining)
        sale_price_per_unit = float(batch.sale_price_per_strip) / units_per_strip
        mrp_per_unit = float(batch.mrp_per_strip) / units_per_strip

        allocations.append(
            {
                "batch": batch,
                "units_to_take": take,
                "sale_price_per_unit": round(sale_price_per_unit, 4),
                "mrp_per_unit": round(mrp_per_unit, 4),
                "gst_rate": float(medicine.gst_rate),
            }
        )
        remaining -= take

    return allocations


async def commit_fefo_allocation(
    db: AsyncSession,
    allocations: list[dict],
) -> None:
    """Deduct sold units from each batch (call only on order confirm)."""
    for alloc in allocations:
        batch: Batch = alloc["batch"]
        batch.sold_units += alloc["units_to_take"]
        batch.available_units -= alloc["units_to_take"]
        db.add(batch)
