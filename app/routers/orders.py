from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.payment import Payment, PaymentMode
from app.schemas.order import OrderCreate, OrderOut, OrderConfirm
from app.services.fefo import get_fefo_batches, commit_fefo_allocation, InsufficientStockError
from app.services.utils import generate_order_number, calculate_line_total

router = APIRouter(prefix="/orders", tags=["Orders"])


# ─────────────────────────────────────────────────────────────
# CREATE DRAFT ORDER
# ─────────────────────────────────────────────────────────────
@router.post("/", response_model=OrderOut, status_code=201)
async def create_order(payload: OrderCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a DRAFT order.
    - FEFO batch allocation is computed and reserved.
    - Stock is NOT deducted yet (happens on confirm).
    """
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
        status=OrderStatus.DRAFT,
        payment_status=PaymentStatus.PENDING,
    )
    db.add(order)
    await db.flush()  # get order.id

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

    # Apply order-level discount on top
    order_disc = subtotal * (payload.discount_percent / 100)
    total_discount += order_disc
    total_amount = subtotal - total_discount + total_gst
    balance = total_amount  # nothing paid yet on draft

    order.subtotal = round(subtotal, 2)
    order.discount_amount = round(total_discount, 2)
    order.gst_amount = round(total_gst, 2)
    order.total_amount = round(total_amount, 2)
    order.balance_amount = round(balance, 2)
    db.add(order)

    await db.flush()
    await db.refresh(order)
    return order


# ─────────────────────────────────────────────────────────────
# CONFIRM ORDER — deducts stock
# ─────────────────────────────────────────────────────────────
@router.post("/{order_id}/confirm", response_model=OrderOut)
async def confirm_order(
    order_id: int,
    payload: OrderConfirm,
    db: AsyncSession = Depends(get_db),
):
    """
    Confirm a DRAFT order:
    1. Deducts stock from batches (FEFO committed).
    2. Records initial payment if provided.
    3. Updates payment_status accordingly.
    """
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    if order.status != OrderStatus.DRAFT:
        raise HTTPException(409, f"Order is already {order.status.value}")

    # Deduct stock for all order items
    for oi in order.items:
        alloc = [
            {
                "batch": await db.get(type("Batch", (), {})(), oi.batch_id) or _get_batch(db, oi.batch_id),
                "units_to_take": oi.quantity_units,
            }
        ]
        # Direct update without re-computing FEFO (items already allocated)
        from app.models.batch import Batch as BatchModel
        batch = await db.get(BatchModel, oi.batch_id)
        if batch:
            batch.sold_units += oi.quantity_units
            batch.available_units -= oi.quantity_units
            db.add(batch)

    order.status = OrderStatus.CONFIRMED
    order.confirmed_at = datetime.now(timezone.utc)

    # Handle initial payment
    if payload.initial_payment > 0:
        payment_amount = min(payload.initial_payment, float(order.total_amount))
        payment = Payment(
            order_id=order.id,
            amount=payment_amount,
            mode=PaymentMode(payload.payment_mode),
            reference_number=payload.payment_reference,
        )
        db.add(payment)
        order.paid_amount = payment_amount
        order.balance_amount = round(float(order.total_amount) - payment_amount, 2)

        if order.balance_amount <= 0:
            order.payment_status = PaymentStatus.PAID
        else:
            order.payment_status = PaymentStatus.PARTIAL
    else:
        order.payment_status = PaymentStatus.PENDING

    db.add(order)
    await db.flush()
    await db.refresh(order)
    return order


# ─────────────────────────────────────────────────────────────
# CANCEL ORDER
# ─────────────────────────────────────────────────────────────
@router.post("/{order_id}/cancel", response_model=OrderOut)
async def cancel_order(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    if order.status == OrderStatus.CONFIRMED:
        raise HTTPException(409, "Confirmed orders cannot be cancelled. Raise a return instead.")
    order.status = OrderStatus.CANCELLED
    db.add(order)
    await db.flush()
    await db.refresh(order)
    return order


# ─────────────────────────────────────────────────────────────
# LIST & GET
# ─────────────────────────────────────────────────────────────
@router.get("/", response_model=list[OrderOut])
async def list_orders(
    status: OrderStatus | None = Query(None),
    payment_status: PaymentStatus | None = Query(None),
    customer_id: int | None = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(Order)
    if status:
        query = query.where(Order.status == status)
    if payment_status:
        query = query.where(Order.payment_status == payment_status)
    if customer_id:
        query = query.where(Order.customer_id == customer_id)

    result = await db.execute(
        query.order_by(Order.created_at.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    return order


async def _get_batch(db, batch_id):
    from app.models.batch import Batch as BatchModel
    return await db.get(BatchModel, batch_id)
