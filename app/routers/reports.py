from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.order import Order, OrderItem
from app.models.medicine import Medicine
from app.models.batch import Batch

router = APIRouter(prefix="/reports", tags=["Reports & Dashboard"])


@router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db)):
    today = date.today()
    start_of_month = today.replace(day=1)

    today_sales = await db.execute(
        select(func.coalesce(func.sum(Order.total_amount), 0))
        .where(
            text("orders.status = 'confirmed'"),
            func.date(Order.confirmed_at) == today,
        )
    )
    month_sales = await db.execute(
        select(func.coalesce(func.sum(Order.total_amount), 0))
        .where(
            text("orders.status = 'confirmed'"),
            func.date(Order.confirmed_at) >= start_of_month,
        )
    )
    pending_balance = await db.execute(
        select(func.coalesce(func.sum(Order.balance_amount), 0))
        .where(
            text("orders.status = 'confirmed'"),
            text("orders.payment_status != 'paid'"),
        )
    )
    total_medicines = await db.execute(
        select(func.count(Medicine.id)).where(Medicine.is_active == True)
    )
    expiry_count = await db.execute(
        select(func.count(Batch.id)).where(
            Batch.is_active == True,
            Batch.available_units > 0,
            Batch.expiry_date >= today,
            Batch.expiry_date <= today + timedelta(days=30),
        )
    )

    return {
        "today_sales":           float(today_sales.scalar()),
        "month_sales":           float(month_sales.scalar()),
        "pending_balance":       float(pending_balance.scalar()),
        "total_medicines":       int(total_medicines.scalar()),
        "expiry_alerts_30_days": int(expiry_count.scalar()),
    }


@router.get("/sales-summary")
async def sales_summary(
    from_date: date = Query(default=date.today().replace(day=1)),
    to_date:   date = Query(default=date.today()),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            func.date(Order.confirmed_at).label("sale_date"),
            func.count(Order.id).label("order_count"),
            func.sum(Order.total_amount).label("total_sales"),
            func.sum(Order.paid_amount).label("total_collected"),
            func.sum(Order.balance_amount).label("total_pending"),
        )
        .where(
            text("orders.status = 'confirmed'"),
            func.date(Order.confirmed_at) >= from_date,
            func.date(Order.confirmed_at) <= to_date,
        )
        .group_by(func.date(Order.confirmed_at))
        .order_by(func.date(Order.confirmed_at).desc())
    )
    rows = result.all()
    return [
        {
            "date":            str(r.sale_date),
            "order_count":     r.order_count,
            "total_sales":     float(r.total_sales or 0),
            "total_collected": float(r.total_collected or 0),
            "total_pending":   float(r.total_pending or 0),
        }
        for r in rows
    ]


@router.get("/top-medicines")
async def top_medicines(
    from_date: date = Query(default=date.today().replace(day=1)),
    to_date:   date = Query(default=date.today()),
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            Medicine.name,
            func.sum(OrderItem.quantity_units).label("units_sold"),
            func.sum(OrderItem.line_total).label("revenue"),
        )
        .join(Order,    OrderItem.order_id    == Order.id)
        .join(Medicine, OrderItem.medicine_id == Medicine.id)
        .where(
            text("orders.status = 'confirmed'"),
            func.date(Order.confirmed_at) >= from_date,
            func.date(Order.confirmed_at) <= to_date,
        )
        .group_by(Medicine.name)
        .order_by(func.sum(OrderItem.line_total).desc())
        .limit(limit)
    )
    rows = result.all()
    return [
        {
            "medicine_name": r.name,
            "units_sold":    int(r.units_sold or 0),
            "revenue":       float(r.revenue or 0),
        }
        for r in rows
    ]