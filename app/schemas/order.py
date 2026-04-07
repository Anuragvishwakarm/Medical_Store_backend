from datetime import datetime
from pydantic import BaseModel, Field
from app.models.order import OrderStatus, PaymentStatus


class OrderItemCreate(BaseModel):
    medicine_id: int
    quantity_units: int = Field(..., ge=1)
    discount_percent: float = Field(0, ge=0, le=100)


class OrderCreate(BaseModel):
    customer_id: int | None = None
    walk_in_name: str | None = None
    walk_in_phone: str | None = None
    prescription_number: str | None = None
    doctor_name: str | None = None
    discount_percent: float = Field(0, ge=0, le=100)
    notes: str | None = None
    items: list[OrderItemCreate] = Field(..., min_length=1)


class OrderItemOut(BaseModel):
    id: int
    medicine_id: int
    batch_id: int
    quantity_units: int
    sale_price_per_unit: float
    mrp_per_unit: float
    discount_percent: float
    gst_rate: float
    line_total: float

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: int
    order_number: str
    customer_id: int | None
    walk_in_name: str | None
    walk_in_phone: str | None
    prescription_number: str | None
    doctor_name: str | None
    status: OrderStatus
    payment_status: PaymentStatus
    subtotal: float
    discount_percent: float
    discount_amount: float
    gst_amount: float
    total_amount: float
    paid_amount: float
    balance_amount: float
    notes: str | None
    items: list[OrderItemOut]
    created_at: datetime
    confirmed_at: datetime | None

    model_config = {"from_attributes": True}


class OrderConfirm(BaseModel):
    """Payload when confirming a draft order."""
    initial_payment: float = Field(0, ge=0)
    payment_mode: str = "cash"
    payment_reference: str | None = None
