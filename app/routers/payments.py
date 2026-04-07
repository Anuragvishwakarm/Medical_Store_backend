from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.order import Order, PaymentStatus, OrderStatus
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentOut

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/", response_model=PaymentOut, status_code=201)
async def add_payment(payload: PaymentCreate, db: AsyncSession = Depends(get_db)):
    """Record a payment against a confirmed order."""
    order = await db.get(Order, payload.order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    if order.status != OrderStatus.CONFIRMED:
        raise HTTPException(409, "Payments can only be added to confirmed orders")
    if order.payment_status == PaymentStatus.PAID:
        raise HTTPException(409, "Order is already fully paid")

    balance = float(order.balance_amount)
    if payload.amount > balance + 0.01:  # small float tolerance
        raise HTTPException(
            422, f"Payment amount ₹{payload.amount} exceeds balance ₹{balance:.2f}"
        )

    payment = Payment(
        order_id=payload.order_id,
        amount=payload.amount,
        mode=payload.mode,
        reference_number=payload.reference_number,
        notes=payload.notes,
    )
    db.add(payment)

    # Update order financials
    order.paid_amount = round(float(order.paid_amount) + payload.amount, 2)
    order.balance_amount = round(float(order.total_amount) - float(order.paid_amount), 2)

    if order.balance_amount <= 0:
        order.payment_status = PaymentStatus.PAID
    elif float(order.paid_amount) > 0:
        order.payment_status = PaymentStatus.PARTIAL

    db.add(order)
    await db.flush()
    await db.refresh(payment)
    return payment


@router.get("/order/{order_id}", response_model=list[PaymentOut])
async def list_order_payments(order_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Payment).where(Payment.order_id == order_id).order_by(Payment.paid_at)
    )
    return result.scalars().all()
