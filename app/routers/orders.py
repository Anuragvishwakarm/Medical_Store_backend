from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.payment import Payment, PaymentMode
from app.schemas.order import OrderCreate, OrderOut, OrderConfirm
from app.services.fefo import get_fefo_batches, InsufficientStockError
from app.services.utils import generate_order_number, calculate_line_total

router = APIRouter(prefix="/orders", tags=["Orders"])


# ── CREATE DRAFT ─────────────────────────────────────────────
@router.post("/", response_model=OrderOut, status_code=201)
async def create_order(payload: OrderCreate, db: AsyncSession = Depends(get_db)):
    order_number = generate_order_number()

    order = Order(
        order_number=order_number,
        customer_id=payload.customer_id,
        walk_in_name=payload.walk_in_name,
        walk_in_phone=payload.walk_in_phone,
        prescription_number=payload.prescription_number,
        doctor_name=payload.doctor_name,
        discount_percent=payload.discount_percent,
        notes=payload.notes,
        status=OrderStatus.draft,               # ← lowercase
        payment_status=PaymentStatus.pending,   # ← lowercase
    )
    db.add(order)
    await db.flush()

    subtotal = 0.0
    total_gst = 0.0
    total_discount = 0.0

    for item in payload.items:
        try:
            allocations = await get_fefo_batches(db, item.medicine_id, item.quantity_units)
        except InsufficientStockError as e:
            raise HTTPException(422, str(e))
        except ValueError as e:
            raise HTTPException(404, str(e))

        for alloc in allocations:
            line_total, gst_amt = calculate_line_total(
                quantity=alloc["units_to_take"],
                price_per_unit=alloc["sale_price_per_unit"],
                discount_percent=item.discount_percent,
                gst_rate=alloc["gst_rate"],
            )
            gross = alloc["units_to_take"] * alloc["sale_price_per_unit"]
            disc_amt = gross * (item.discount_percent / 100)

            subtotal += gross
            total_discount += disc_amt
            total_gst += gst_amt

            order_item = OrderItem(
                order_id=order.id,
                medicine_id=item.medicine_id,
                batch_id=alloc["batch"].id,
                quantity_units=alloc["units_to_take"],
                sale_price_per_unit=alloc["sale_price_per_unit"],
                mrp_per_unit=alloc["mrp_per_unit"],
                discount_percent=item.discount_percent,
                gst_rate=alloc["gst_rate"],
                line_total=line_total,
            )
            db.add(order_item)

    order_disc = subtotal * (payload.discount_percent / 100)
    total_discount += order_disc
    total_amount = subtotal - total_discount + total_gst
    balance = total_amount

    order.subtotal = round(subtotal, 2)
    order.discount_amount = round(total_discount, 2)
    order.gst_amount = round(total_gst, 2)
    order.total_amount = round(total_amount, 2)
    order.balance_amount = round(balance, 2)
    db.add(order)

    await db.flush()
    await db.refresh(order)
    return order


# ── CONFIRM ───────────────────────────────────────────────────
@router.post("/{order_id}/confirm", response_model=OrderOut)
async def confirm_order(
    order_id: int,
    payload: OrderConfirm,
    db: AsyncSession = Depends(get_db),
):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    if order.status != OrderStatus.draft:         # ← lowercase
        raise HTTPException(409, f"Order is already {order.status.value}")

    # Deduct stock
    from app.models.batch import Batch as BatchModel
    for oi in order.items:
        batch = await db.get(BatchModel, oi.batch_id)
        if batch:
            batch.sold_units += oi.quantity_units
            batch.available_units -= oi.quantity_units
            db.add(batch)

    order.status = OrderStatus.confirmed          # ← lowercase
    order.confirmed_at = datetime.now(timezone.utc)

    if payload.initial_payment > 0:
        pay_amt = min(payload.initial_payment, float(order.total_amount))
        payment = Payment(
            order_id=order.id,
            amount=pay_amt,
            mode=PaymentMode(payload.payment_mode),
            reference_number=payload.payment_reference,
        )
        db.add(payment)
        order.paid_amount = pay_amt
        order.balance_amount = round(float(order.total_amount) - pay_amt, 2)
        order.payment_status = (
            PaymentStatus.paid if order.balance_amount <= 0 else PaymentStatus.partial  # ← lowercase
        )
    else:
        order.payment_status = PaymentStatus.pending    # ← lowercase

    db.add(order)
    await db.flush()
    await db.refresh(order)
    return order


# ── CANCEL ────────────────────────────────────────────────────
@router.post("/{order_id}/cancel", response_model=OrderOut)
async def cancel_order(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    if order.status == OrderStatus.confirmed:     # ← lowercase
        raise HTTPException(409, "Confirmed orders cannot be cancelled.")
    order.status = OrderStatus.cancelled          # ← lowercase
    db.add(order)
    await db.flush()
    await db.refresh(order)
    return order


# ── LIST ──────────────────────────────────────────────────────
@router.get("/", response_model=list[OrderOut])
async def list_orders(
    status: str | None = Query(None),
    payment_status: str | None = Query(None),
    customer_id: int | None = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import text
    query = select(Order)
    if status:
        query = query.where(text(f"orders.status = '{status}'"))
    if payment_status:
        query = query.where(text(f"orders.payment_status = '{payment_status}'"))
    if customer_id:
        query = query.where(Order.customer_id == customer_id)

    result = await db.execute(
        query.order_by(Order.created_at.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()


# ── GET ONE ───────────────────────────────────────────────────
@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    return order